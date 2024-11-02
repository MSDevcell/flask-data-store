from flask_restx import fields
from api.namespaces import items_ns, media_ns

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
