from app import app, db
from models import FunctionDefinition, FunctionVersion, FunctionExecution

def run_migrations():
    """Run database migrations"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully")

if __name__ == "__main__":
    run_migrations()
