from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

class Item(db.Model):
    """Data store item model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MediaFile(db.Model):
    """Media file model for smart device multimedia"""
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(100), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=False)
    deletion_time = db.Column(db.DateTime, nullable=False)
    content_type = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'sender_name': self.sender_name,
            'data_type': self.data_type,
            'timestamp': self.timestamp.isoformat(),
            'file_path': self.file_path,
            'deletion_time': self.deletion_time.isoformat(),
            'content_type': self.content_type
        }

class FunctionDefinition(db.Model):
    """Dynamic function definition model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    parameters = db.Column(JSON)
    status = db.Column(db.String(20), default='active')  # active, disabled, error
    
    # Relationships
    versions = relationship("FunctionVersion", back_populates="function", order_by="desc(FunctionVersion.version_number)")
    executions = relationship("FunctionExecution", back_populates="function")

    def to_dict(self):
        latest_version = self.versions[0] if self.versions else None
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'parameters': self.parameters,
            'status': self.status,
            'current_version': latest_version.version_number if latest_version else None,
            'total_executions': len(self.executions)
        }

class FunctionVersion(db.Model):
    """Version control for function definitions"""
    id = db.Column(db.Integer, primary_key=True)
    function_id = db.Column(db.Integer, db.ForeignKey('function_definition.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    code = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    function = relationship("FunctionDefinition", back_populates="versions")

    __table_args__ = (
        db.UniqueConstraint('function_id', 'version_number', name='unique_function_version'),
    )

class FunctionExecution(db.Model):
    """Function execution history"""
    id = db.Column(db.Integer, primary_key=True)
    function_id = db.Column(db.Integer, db.ForeignKey('function_definition.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    parameters = db.Column(JSON)
    result = db.Column(JSON)
    status = db.Column(db.String(20), nullable=False)  # success, error, timeout
    error_message = db.Column(db.Text)
    execution_time = db.Column(db.Float)  # in seconds
    memory_usage = db.Column(db.Float)  # in MB
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship
    function = relationship("FunctionDefinition", back_populates="executions")
