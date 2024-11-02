from flask import request, make_response, render_template, jsonify
from flask_restx import Resource
from app import db
from models import Item
from api.serializers import item_model, item_input_model
from utils.validators import validate_item_input
import csv
from io import StringIO
import logging
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds

def register_routes(ns):
    @ns.route('/')
    class ItemList(Resource):
        @ns.doc('list_items')
        @ns.marshal_list_with(item_model)
        def get(self):
            """List all items"""
            try:
                items = Item.query.all()
                logger.debug(f"Retrieved {len(items)} items")
                return items
            except SQLAlchemyError as e:
                logger.error(f"Database error when listing items: {str(e)}")
                return [], 500

        @ns.doc('create_item')
        @ns.expect(item_input_model)
        @ns.marshal_with(item_model, code=201)
        def post(self):
            """Create a new item"""
            try:
                data = request.json
                validate_item_input(data)
                
                item = Item(
                    title=data['title'],
                    description=data.get('description', '')
                )
                db.session.add(item)
                db.session.commit()
                logger.info(f"Created new item with id: {item.id}")
                return item, 201
            except SQLAlchemyError as e:
                logger.error(f"Database error when creating item: {str(e)}")
                db.session.rollback()
                return {'error': 'Database error occurred', 'message': str(e)}, 500

    @ns.route('/string-type')
    class StringItems(Resource):
        def try_connect(self):
            """Try to establish database connection with retries"""
            for attempt in range(MAX_RETRIES):
                try:
                    db.session.execute(db.text('SELECT 1'))
                    logger.info("Database connection successful")
                    return True
                except OperationalError as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Database connection attempt {attempt + 1} failed, retrying...")
                        time.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        logger.error(f"Database connection failed after {MAX_RETRIES} attempts: {str(e)}")
                        return False
            return False

        @ns.doc('get_string_items')
        @ns.marshal_list_with(item_model)
        def get(self):
            """Get all items sorted by creation time (newest first)"""
            try:
                logger.info("Checking database connection")
                if not self.try_connect():
                    return jsonify({
                        'error': 'Database connection failed',
                        'message': 'Unable to establish database connection'
                    }), 503

                logger.info("Fetching string-type items")
                items = Item.query.order_by(Item.created_at.desc()).all()
                logger.info(f"Successfully retrieved {len(items)} items")
                
                # Return empty list if no items found
                if not items:
                    logger.info("No items found")
                    return []
                
                return items
                
            except DatabaseError as e:
                logger.error(f"Database error in string-type items: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'error': 'Database error',
                    'message': str(e)
                }), 500
            except Exception as e:
                logger.error(f"Unexpected error in string-type items: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'message': str(e)
                }), 500
            finally:
                try:
                    db.session.close()
                    logger.debug("Database session closed")
                except Exception as e:
                    logger.error(f"Error closing database session: {str(e)}")

    @ns.route('/export')
    class ItemExport(Resource):
        @ns.doc('export_items', 
               description='Export all items as CSV file',
               responses={200: 'Success - Returns a CSV file with all items'})
        def get(self):
            """Export all items as CSV"""
            try:
                items = Item.query.all()
                logger.info(f"Exporting {len(items)} items to CSV")
                
                si = StringIO()
                writer = csv.writer(si)
                
                writer.writerow(['ID', 'Title', 'Description', 'Created At', 'Updated At'])
                
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
            except SQLAlchemyError as e:
                logger.error(f"Database error when exporting items: {str(e)}")
                return {'error': 'Database error occurred', 'message': str(e)}, 500

    @ns.route('/<int:id>')
    @ns.response(404, 'Item not found')
    @ns.param('id', 'The item identifier')
    class ItemResource(Resource):
        @ns.doc('get_item')
        @ns.marshal_with(item_model)
        def get(self, id):
            """Fetch an item by ID"""
            try:
                item = Item.query.get_or_404(id)
                logger.debug(f"Retrieved item {id}: {item.title}")
                return item
            except SQLAlchemyError as e:
                logger.error(f"Database error when fetching item {id}: {str(e)}")
                return {'error': 'Database error occurred', 'message': str(e)}, 500

        @ns.doc('update_item')
        @ns.expect(item_input_model)
        @ns.marshal_with(item_model)
        def put(self, id):
            """Update an item"""
            try:
                item = Item.query.get_or_404(id)
                data = request.json
                validate_item_input(data)
                
                item.title = data['title']
                item.description = data.get('description', item.description)
                db.session.commit()
                logger.info(f"Updated item {id}")
                return item
            except SQLAlchemyError as e:
                logger.error(f"Database error when updating item {id}: {str(e)}")
                db.session.rollback()
                return {'error': 'Database error occurred', 'message': str(e)}, 500

        @ns.doc('delete_item')
        @ns.response(204, 'Item deleted')
        def delete(self, id):
            """Delete an item"""
            try:
                item = Item.query.get_or_404(id)
                db.session.delete(item)
                db.session.commit()
                logger.info(f"Deleted item {id}")
                return '', 204
            except SQLAlchemyError as e:
                logger.error(f"Database error when deleting item {id}: {str(e)}")
                db.session.rollback()
                return {'error': 'Database error occurred', 'message': str(e)}, 500

    # Chat interface route
    @ns.route('/chat')
    class ChatInterface(Resource):
        @ns.doc('chat_interface')
        def get(self):
            """Render chat interface"""
            try:
                return make_response(render_template('chat.html'))
            except Exception as e:
                logger.error(f"Error rendering chat interface: {str(e)}")
                return {'error': 'Error rendering chat interface', 'message': str(e)}, 500
