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
MAX_RETRY_BACKOFF = 5  # seconds

def try_database_operation(operation, max_retries=MAX_RETRIES):
    """Execute database operation with retry logic"""
    for attempt in range(max_retries):
        try:
            return operation(), None
        except OperationalError as e:
            if attempt < max_retries - 1:
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_BACKOFF)
                logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {str(e)}")
                time.sleep(delay)
            else:
                logger.error(f"Database operation failed after {max_retries} attempts: {str(e)}")
                return None, str(e)
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return None, str(e)

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
            logger.info("Received POST request to create new item")
            data = request.json
            logger.debug(f"Request payload: {data}")

            try:
                # Validate input
                validate_item_input(data)
                logger.debug("Input validation successful")
                
                # Start transaction
                item = Item(
                    title=data['title'],
                    description=data.get('description', '')
                )
                logger.info(f"Creating new item with title: {item.title}")
                
                def db_operation():
                    db.session.add(item)
                    db.session.commit()
                    return item

                result, error = try_database_operation(db_operation)
                
                if error:
                    logger.error(f"Failed to create item: {error}")
                    return {'error': 'Database error occurred', 'message': error}, 500
                
                logger.info(f"Successfully created item with id: {result.id}")
                return result, 201

            except Exception as e:
                logger.error(f"Unexpected error creating item: {str(e)}")
                db.session.rollback()
                return {'error': 'Error occurred', 'message': str(e)}, 500

    @ns.route('/string-type')
    class StringItems(Resource):
        def try_connect(self):
            """Try to establish database connection with retries"""
            logger.info("Attempting to establish database connection")
            
            def check_connection():
                db.session.execute(db.text('SELECT 1'))
                return True

            result, error = try_database_operation(check_connection)
            if error:
                logger.error(f"Database connection failed: {error}")
                return False
            
            logger.info("Database connection successful")
            return True

        @ns.doc('get_string_items')
        @ns.marshal_list_with(item_model)
        def get(self):
            """Get all items sorted by creation time (newest first)"""
            try:
                # Check database connection
                if not self.try_connect():
                    logger.error("Failed to establish database connection")
                    return jsonify({
                        'error': 'Database connection failed',
                        'message': 'Unable to establish database connection'
                    }), 503

                logger.info("Fetching speech items")
                
                def fetch_items():
                    return Item.query.filter_by(description='speech').order_by(Item.created_at.desc()).all()

                items, error = try_database_operation(fetch_items)
                
                if error:
                    logger.error(f"Error fetching speech items: {error}")
                    return jsonify({
                        'error': 'Database error',
                        'message': error
                    }), 500

                # Debug logging for found items
                logger.debug(f"Found {len(items)} speech items:")
                for item in items:
                    logger.debug(f"Item {item.id}: {item.title} (created: {item.created_at})")
                
                # Return empty list if no items found
                if not items:
                    logger.info("No speech items found")
                    return []
                
                logger.info(f"Successfully retrieved {len(items)} speech items")
                return items

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
