from flask_restx import fields
from api.namespaces import items_ns

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
