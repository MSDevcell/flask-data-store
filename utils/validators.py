from flask_restx import abort

def validate_item_input(data):
    """Validate item input data"""
    if not data.get('title'):
        abort(400, message="Title is required")
    if len(data['title']) > 100:
        abort(400, message="Title must be less than 100 characters")
    return True
