from flask_restx import fields
from api.namespaces import items_ns, media_ns, functions_ns

# Request/Response models for swagger documentation
item_model = items_ns.model('Item', {
    'id': fields.Integer(readonly=True, description='Item identifier'),
    'title': fields.String(required=True, description='Item title'),
    'description': fields.String(description='Item description'),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True)
})

item_input_model = items_ns.model('ItemInput', {
    'title': fields.String(required=True, description='Item title'),
    'description': fields.String(description='Item description')
})

# Media file models
media_file_model = media_ns.model('MediaFile', {
    'id': fields.Integer(readonly=True, description='Media file identifier'),
    'sender_name': fields.String(description='Name of the sender (optional, defaults to "anonymous")'),
    'data_type': fields.String(description='Type of media data (optional, auto-detected from file type: image, video, audio, document)'),
    'timestamp': fields.DateTime(readonly=True, description='Upload timestamp (auto-generated)'),
    'file_path': fields.String(readonly=True, description='Server path where file is stored'),
    'deletion_time': fields.DateTime(description='Scheduled deletion time (optional, defaults to 24 hours from upload)'),
    'content_type': fields.String(readonly=True, description='MIME type of the content (auto-detected from file)')
})

media_upload_model = media_ns.model('MediaUpload', {
    'file': fields.Raw(required=True, description='Media file to upload (max size: 10MB, allowed types: png, jpg, jpeg, gif, mp4, mp3, wav, pdf, doc, docx)'),
    'sender_name': fields.String(required=False, description='Name of the sender (optional, defaults to "anonymous")'),
    'data_type': fields.String(required=False, description='Type of media data (optional, auto-detected from file type)'),
    'deletion_time': fields.DateTime(required=False, description='When the file should be deleted (optional, ISO format, defaults to 24 hours from upload)')
})

# Function models
parameter_schema = functions_ns.model('ParameterSchema', {
    'type': fields.String(required=True, enum=['string', 'integer', 'float', 'boolean', 'list', 'dict'], 
                         description='Parameter type'),
    'required': fields.Boolean(required=True, description='Whether the parameter is required'),
    'description': fields.String(description='Parameter description'),
    'range': fields.Raw(description='Value range for numeric parameters (min, max)'),
    'default': fields.Raw(description='Default value')
})

function_model = functions_ns.model('Function', {
    'id': fields.Integer(readonly=True, description='Function identifier'),
    'name': fields.String(required=True, description='Function name'),
    'description': fields.String(description='Function description'),
    'created_at': fields.DateTime(readonly=True),
    'is_active': fields.Boolean(description='Function activation status'),
    'parameters': fields.Raw(description='Function parameters schema'),
    'status': fields.String(description='Function status (active, disabled, error)'),
    'current_version': fields.Integer(readonly=True, description='Current version number'),
    'total_executions': fields.Integer(readonly=True, description='Total number of executions')
})

function_input_model = functions_ns.model('FunctionInput', {
    'name': fields.String(required=True, description='Function name'),
    'code': fields.String(required=True, description='Function code'),
    'description': fields.String(description='Function description'),
    'parameters': fields.Nested(parameter_schema, as_list=False, description='Function parameters schema')
})

function_execute_model = functions_ns.model('FunctionExecute', {
    'parameters': fields.Raw(required=True, description='Function parameters')
})

function_version_model = functions_ns.model('FunctionVersion', {
    'id': fields.Integer(readonly=True),
    'version_number': fields.Integer(readonly=True),
    'code': fields.String(readonly=True),
    'created_at': fields.DateTime(readonly=True)
})

function_execution_model = functions_ns.model('FunctionExecution', {
    'id': fields.Integer(readonly=True),
    'version_number': fields.Integer(readonly=True),
    'parameters': fields.Raw(readonly=True),
    'result': fields.Raw(readonly=True),
    'status': fields.String(readonly=True),
    'error_message': fields.String(readonly=True),
    'execution_time': fields.Float(readonly=True),
    'memory_usage': fields.Float(readonly=True),
    'started_at': fields.DateTime(readonly=True),
    'completed_at': fields.DateTime(readonly=True)
})
