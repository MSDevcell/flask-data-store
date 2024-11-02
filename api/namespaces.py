from flask_restx import Namespace

# Create API namespaces
items_ns = Namespace('items', description='Items operations')
media_ns = Namespace('media', description='Media file operations')

def register_namespaces(api):
    """Register all API namespaces"""
    from api.routes import register_routes
    from api.media_routes import register_media_routes
    
    register_routes(items_ns)
    register_media_routes(media_ns)
    
    api.add_namespace(items_ns, path='/api/items')
    api.add_namespace(media_ns, path='/api/media')
