from flask_restx import Namespace

# Create API namespaces
items_ns = Namespace('items', description='Items operations')

def register_namespaces(api):
    """Register all API namespaces"""
    from api.routes import register_routes
    register_routes(items_ns)
    api.add_namespace(items_ns, path='/api/items')
