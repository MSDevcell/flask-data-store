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
    'sender_name': fields.String(required=True, description='Name of the sender'),
    'data_type': fields.String(required=True, description='Type of media data'),
    'timestamp': fields.DateTime(readonly=True),
    'file_path': fields.String(readonly=True),
    'deletion_time': fields.DateTime(required=True, description='When the file should be deleted'),
    'content_type': fields.String(required=True, description='MIME type of the content')
})

media_upload_model = media_ns.model('MediaUpload', {
    'sender_name': fields.String(required=True, description='Name of the sender'),
    'data_type': fields.String(required=True, description='Type of media data'),
    'deletion_time': fields.DateTime(required=True, description='When the file should be deleted')
})

# Function definition models
function_model = functions_ns.model('Function', {
    'id': fields.Integer(readonly=True, description='Function identifier'),
    'name': fields.String(required=True, description='Function name'),
    'description': fields.String(description='Function description'),
    'created_at': fields.DateTime(readonly=True),
    'is_active': fields.Boolean(description='Function activation status'),
    'parameters': fields.Raw(description='Function parameters schema')
})

function_input_model = functions_ns.model('FunctionInput', {
    'name': fields.String(required=True, description='Function name'),
    'code': fields.String(required=True, description='Function code'),
    'description': fields.String(description='Function description'),
    'parameters': fields.Raw(description='Function parameters schema')
})

function_execute_model = functions_ns.model('FunctionExecute', {
    'parameters': fields.Raw(required=True, description='Function parameters')
})
