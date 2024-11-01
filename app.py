import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Setup configurations
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)

# Initialize API with swagger
api = Api(
    app,
    version='1.0',
    title='Data Store API',
    description='A Flask-based REST API with automatic Swagger documentation',
    doc='/docs'
)

with app.app_context():
    from api.namespaces import register_namespaces
    register_namespaces(api)
    import models
    db.create_all()
