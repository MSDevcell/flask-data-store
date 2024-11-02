from datetime import datetime
from app import db

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
