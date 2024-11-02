from flask import request
from flask_restx import Resource
import ast
import inspect
import time
import resource
import signal
from datetime import datetime
from threading import Thread
import psutil
from app import db
from models import FunctionDefinition, FunctionVersion, FunctionExecution
from api.serializers import (
    function_model, function_input_model, function_execute_model,
    function_version_model, function_execution_model
)

# Constants for execution limits
MAX_EXECUTION_TIME = 5  # seconds
MAX_MEMORY_USAGE = 100  # MB
SUPPORTED_PARAMETER_TYPES = {
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool,
    'list': list,
    'dict': dict
}

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function execution timed out")

def validate_parameter_schema(parameters):
    """Validate parameter schema structure"""
    if not isinstance(parameters, dict):
        return False, "Parameters schema must be a dictionary"
    
    for param_name, param_spec in parameters.items():
        if not isinstance(param_spec, dict):
            return False, f"Parameter specification for '{param_name}' must be a dictionary"
        
        required_fields = ['type', 'required']
        for field in required_fields:
            if field not in param_spec:
                return False, f"Missing '{field}' in parameter '{param_name}' specification"
        
        if param_spec['type'] not in SUPPORTED_PARAMETER_TYPES:
            return False, f"Unsupported type '{param_spec['type']}' for parameter '{param_name}'"
        
        if 'range' in param_spec:
            range_spec = param_spec['range']
            if not isinstance(range_spec, dict) or 'min' not in range_spec or 'max' not in range_spec:
                return False, f"Invalid range specification for parameter '{param_name}'"
    
    return True, None

def validate_parameters(parameters, schema):
    """Validate parameters against schema"""
    for param_name, param_spec in schema.items():
        # Check required parameters
        if param_spec.get('required', False) and param_name not in parameters:
            return False, f"Required parameter '{param_name}' is missing"
        
        if param_name in parameters:
            param_value = parameters[param_name]
            expected_type = SUPPORTED_PARAMETER_TYPES[param_spec['type']]
            
            # Type checking
            if not isinstance(param_value, expected_type):
                return False, f"Parameter '{param_name}' must be of type {param_spec['type']}"
            
            # Range validation
            if 'range' in param_spec and param_spec['type'] in ['integer', 'float']:
                range_spec = param_spec['range']
                if param_value < range_spec['min'] or param_value > range_spec['max']:
                    return False, f"Parameter '{param_name}' must be between {range_spec['min']} and {range_spec['max']}"
    
    return True, None

def is_safe_code(code):
    """Validate if the code is safe to execute"""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Check for imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False, "Import statements are not allowed"
            # Check for file operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ['open', 'eval', 'exec']:
                    return False, "File operations and code execution are not allowed"
                if isinstance(node.func, ast.Attribute) and node.func.attr in ['read', 'write', 'delete']:
                    return False, "File operations are not allowed"
        
        # Validate function signature
        lines = code.strip().split('\n')
        first_line = lines[0]
        if not first_line.startswith('def process'):
            return False, "Function must be named 'process'"
        
        func_def = ast.parse(code).body[0]
        if not isinstance(func_def, ast.FunctionDef):
            return False, "Code must define a function"
        
        args = func_def.args
        if len(args.args) != 1 or args.args[0].arg != 'parameters':
            return False, "Function must accept exactly one argument named 'parameters'"
            
        return True, "Code is safe"
    except SyntaxError:
        return False, "Invalid Python syntax"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def execute_function_safely(code, parameters):
    """Execute function with safety measures"""
    def monitor_resources():
        process = psutil.Process()
        while True:
            memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
            if memory_usage > MAX_MEMORY_USAGE:
                raise MemoryError(f"Memory usage exceeded limit of {MAX_MEMORY_USAGE}MB")
            time.sleep(0.1)

    # Set resource limits
    resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_USAGE * 1024 * 1024, -1))
    
    # Set up timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(MAX_EXECUTION_TIME)
    
    start_time = time.time()
    memory_usage = 0
    result = None
    error = None
    
    try:
        # Start resource monitoring in a separate thread
        monitor_thread = Thread(target=monitor_resources)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Create function namespace
        namespace = {}
        exec(code, namespace)
        
        if 'process' not in namespace:
            raise ValueError("Function 'process' not found in the code")
        
        # Execute the function
        result = namespace['process'](parameters)
        
    except TimeoutError as e:
        error = str(e)
    except MemoryError as e:
        error = str(e)
    except Exception as e:
        error = str(e)
    finally:
        signal.alarm(0)  # Disable the alarm
        execution_time = time.time() - start_time
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024
        except:
            pass
    
    return result, error, execution_time, memory_usage

def register_function_routes(ns):
    @ns.route('/')
    class FunctionList(Resource):
        @ns.doc('list_functions')
        @ns.marshal_list_with(function_model)
        def get(self):
            """List all available functions"""
            return FunctionDefinition.query.filter_by(is_active=True).all()

        @ns.doc('create_function')
        @ns.expect(function_input_model)
        @ns.marshal_with(function_model, code=201)
        def post(self):
            """Upload a new function definition"""
            data = request.json
            
            # Validate parameter schema
            is_valid, message = validate_parameter_schema(data.get('parameters', {}))
            if not is_valid:
                ns.abort(400, f"Invalid parameter schema: {message}")
            
            # Validate code safety
            is_safe, message = is_safe_code(data['code'])
            if not is_safe:
                ns.abort(400, f"Code validation failed: {message}")
            
            try:
                # Create function definition
                function = FunctionDefinition(
                    name=data['name'],
                    description=data.get('description', ''),
                    parameters=data.get('parameters', {}),
                    status='active'
                )
                
                db.session.add(function)
                db.session.flush()  # Get function ID
                
                # Create initial version
                version = FunctionVersion(
                    function_id=function.id,
                    version_number=1,
                    code=data['code']
                )
                
                db.session.add(version)
                db.session.commit()
                return function, 201
                
            except Exception as e:
                db.session.rollback()
                ns.abort(500, f"Error creating function: {str(e)}")

    @ns.route('/<string:name>')
    @ns.response(404, 'Function not found')
    class FunctionResource(Resource):
        @ns.doc('get_function')
        @ns.marshal_with(function_model)
        def get(self, name):
            """Get function details"""
            return FunctionDefinition.query.filter_by(name=name, is_active=True).first_or_404()

        @ns.doc('update_function')
        @ns.expect(function_input_model)
        @ns.marshal_with(function_model)
        def put(self, name):
            """Update function"""
            function = FunctionDefinition.query.filter_by(name=name, is_active=True).first_or_404()
            data = request.json
            
            try:
                # Validate code if provided
                if 'code' in data:
                    is_safe, message = is_safe_code(data['code'])
                    if not is_safe:
                        ns.abort(400, f"Code validation failed: {message}")
                    
                    # Create new version
                    latest_version = max([v.version_number for v in function.versions])
                    version = FunctionVersion(
                        function_id=function.id,
                        version_number=latest_version + 1,
                        code=data['code']
                    )
                    db.session.add(version)
                
                # Update other fields
                if 'description' in data:
                    function.description = data['description']
                if 'parameters' in data:
                    is_valid, message = validate_parameter_schema(data['parameters'])
                    if not is_valid:
                        ns.abort(400, f"Invalid parameter schema: {message}")
                    function.parameters = data['parameters']
                
                db.session.commit()
                return function
                
            except Exception as e:
                db.session.rollback()
                ns.abort(500, f"Error updating function: {str(e)}")

        @ns.doc('delete_function')
        @ns.response(204, 'Function deleted')
        def delete(self, name):
            """Delete function"""
            function = FunctionDefinition.query.filter_by(name=name, is_active=True).first_or_404()
            try:
                function.is_active = False
                function.status = 'disabled'
                db.session.commit()
                return '', 204
            except Exception as e:
                db.session.rollback()
                ns.abort(500, f"Error deleting function: {str(e)}")

    @ns.route('/<string:name>/execute')
    @ns.response(404, 'Function not found')
    class FunctionExecution(Resource):
        @ns.doc('execute_function')
        @ns.expect(function_execute_model)
        def post(self, name):
            """Execute function"""
            function = FunctionDefinition.query.filter_by(name=name, is_active=True).first_or_404()
            
            if function.status != 'active':
                ns.abort(400, f"Function is {function.status}")
            
            latest_version = function.versions[0]
            parameters = request.json.get('parameters', {})
            
            # Validate parameters
            is_valid, message = validate_parameters(parameters, function.parameters)
            if not is_valid:
                ns.abort(400, f"Parameter validation failed: {message}")
            
            try:
                # Execute function safely
                result, error, execution_time, memory_usage = execute_function_safely(
                    latest_version.code, parameters
                )
                
                # Record execution
                execution = FunctionExecution(
                    function_id=function.id,
                    version_number=latest_version.version_number,
                    parameters=parameters,
                    result=result if not error else None,
                    status='error' if error else 'success',
                    error_message=error,
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                
                db.session.add(execution)
                db.session.commit()
                
                if error:
                    return {'error': error}, 500
                return {'result': result}
                
            except Exception as e:
                db.session.rollback()
                ns.abort(500, f"Error executing function: {str(e)}")

    @ns.route('/<string:name>/versions')
    @ns.response(404, 'Function not found')
    class FunctionVersions(Resource):
        @ns.doc('get_versions')
        @ns.marshal_list_with(function_version_model)
        def get(self, name):
            """Get function versions"""
            function = FunctionDefinition.query.filter_by(name=name, is_active=True).first_or_404()
            return function.versions

    @ns.route('/<string:name>/executions')
    @ns.response(404, 'Function not found')
    class FunctionExecutions(Resource):
        @ns.doc('get_executions')
        @ns.marshal_list_with(function_execution_model)
        def get(self, name):
            """Get function execution history"""
            function = FunctionDefinition.query.filter_by(name=name, is_active=True).first_or_404()
            return function.executions
