from flask import request
from flask_restx import Resource
import ast
import inspect
from app import db
from models import FunctionDefinition
from api.serializers import function_model, function_input_model, function_execute_model

def is_safe_code(code):
    """
    Validate if the code is safe to execute by checking for dangerous operations
    """
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
        
        # Check if the function accepts only the parameters argument
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
            
            # Validate code safety
            is_safe, message = is_safe_code(data['code'])
            if not is_safe:
                ns.abort(400, f"Code validation failed: {message}")
            
            # Check if function name already exists
            if FunctionDefinition.query.filter_by(name=data['name']).first():
                ns.abort(400, "Function name already exists")
            
            function = FunctionDefinition(
                name=data['name'],
                code=data['code'],
                description=data.get('description', ''),
                parameters=data.get('parameters', {}),
                is_active=True
            )
            
            db.session.add(function)
            db.session.commit()
            return function, 201

    @ns.route('/<string:name>')
    @ns.response(404, 'Function not found')
    class FunctionResource(Resource):
        @ns.doc('delete_function')
        @ns.response(204, 'Function deleted')
        def delete(self, name):
            """Delete a function"""
            function = FunctionDefinition.query.filter_by(name=name).first_or_404()
            function.is_active = False
            db.session.commit()
            return '', 204

    @ns.route('/<string:name>/execute')
    @ns.response(404, 'Function not found')
    class FunctionExecution(Resource):
        @ns.doc('execute_function')
        @ns.expect(function_execute_model)
        def post(self, name):
            """Execute a function"""
            function = FunctionDefinition.query.filter_by(name=name, is_active=True).first_or_404()
            
            # Create function namespace
            namespace = {}
            
            try:
                # Execute the function code in the namespace
                exec(function.code, namespace)
                
                # Get the process function
                if 'process' not in namespace:
                    ns.abort(500, "Function 'process' not found in the code")
                
                process_func = namespace['process']
                
                # Execute the function with parameters
                result = process_func(request.json.get('parameters', {}))
                return {'result': result}
            
            except Exception as e:
                ns.abort(500, f"Function execution failed: {str(e)}")
