from flask import request
from flask_restx import Resource
from app import db
from models import Item
from api.serializers import item_model, item_input_model
from utils.validators import validate_item_input

def register_routes(ns):
    @ns.route('/')
    class ItemList(Resource):
        @ns.doc('list_items')
        @ns.marshal_list_with(item_model)
        def get(self):
            """List all items"""
            return Item.query.all()

        @ns.doc('create_item')
        @ns.expect(item_input_model)
        @ns.marshal_with(item_model, code=201)
        def post(self):
            """Create a new item"""
            data = request.json
            validate_item_input(data)
            
            item = Item(
                title=data['title'],
                description=data.get('description', '')
            )
            db.session.add(item)
            db.session.commit()
            return item, 201

    @ns.route('/<int:id>')
    @ns.response(404, 'Item not found')
    @ns.param('id', 'The item identifier')
    class ItemResource(Resource):
        @ns.doc('get_item')
        @ns.marshal_with(item_model)
        def get(self, id):
            """Fetch an item by ID"""
            item = Item.query.get_or_404(id)
            return item

        @ns.doc('update_item')
        @ns.expect(item_input_model)
        @ns.marshal_with(item_model)
        def put(self, id):
            """Update an item"""
            item = Item.query.get_or_404(id)
            data = request.json
            validate_item_input(data)
            
            item.title = data['title']
            item.description = data.get('description', item.description)
            db.session.commit()
            return item

        @ns.doc('delete_item')
        @ns.response(204, 'Item deleted')
        def delete(self, id):
            """Delete an item"""
            item = Item.query.get_or_404(id)
            db.session.delete(item)
            db.session.commit()
            return '', 204
