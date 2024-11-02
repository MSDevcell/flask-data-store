from flask import request, make_response, render_template
from flask_restx import Resource
from app import db
from models import Item
from api.serializers import item_model, item_input_model
from utils.validators import validate_item_input
import csv
from io import StringIO

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

    @ns.route('/string-type')
    class StringItems(Resource):
        @ns.doc('get_string_items')
        @ns.marshal_list_with(item_model)
        def get(self):
            """Get all items sorted by creation time (newest first)"""
            return Item.query.order_by(Item.created_at.desc()).all()

    @ns.route('/export')
    class ItemExport(Resource):
        @ns.doc('export_items', 
               description='Export all items as CSV file',
               responses={200: 'Success - Returns a CSV file with all items'})
        def get(self):
            """Export all items as CSV"""
            items = Item.query.all()
            
            # Create a string buffer to write CSV data
            si = StringIO()
            writer = csv.writer(si)
            
            # Write headers
            writer.writerow(['ID', 'Title', 'Description', 'Created At', 'Updated At'])
            
            # Write item data
            for item in items:
                writer.writerow([
                    item.id,
                    item.title,
                    item.description,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat()
                ])
            
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=items_export.csv"
            output.headers["Content-type"] = "text/csv"
            return output

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

    # Chat interface route
    @ns.route('/chat')
    class ChatInterface(Resource):
        @ns.doc('chat_interface')
        def get(self):
            """Render chat interface"""
            try:
                return make_response(render_template('chat.html'))
            except Exception as e:
                return {'error': str(e)}, 500
