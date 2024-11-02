import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from sqlalchemy.orm import DeclarativeBase
from flask_apscheduler import APScheduler
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
scheduler = APScheduler()
app = Flask(__name__)

# Enable CORS
CORS(app)

# Setup configurations
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
scheduler.init_app(app)
scheduler.start()

# Initialize API with swagger
api = Api(
    app,
    version='1.0',
    title='Smart Device Multimedia API',
    description='A Flask-based REST API for managing multimedia files with automatic deletion',
    doc='/docs'
)

with app.app_context():
    from api.namespaces import register_namespaces
    register_namespaces(api)
    import models
    
    try:
        logger.info("Attempting to create database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
    
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Schedule automatic file deletion task
    from api.media_routes import delete_expired_files
    scheduler.add_job(id='delete_expired_files', 
                     func=delete_expired_files,
                     trigger='interval',
                     minutes=5)  # Run every 5 minutes

# Add error handlers
@app.errorhandler(500)
def handle_500_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    return {"error": "Internal Server Error", "message": str(error)}, 500

@app.errorhandler(404)
def handle_404_error(error):
    return {"error": "Not Found", "message": str(error)}, 404
