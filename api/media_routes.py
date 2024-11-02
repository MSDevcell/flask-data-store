from datetime import datetime, timedelta
from flask import request, current_app
from flask_restx import Resource
from werkzeug.utils import secure_filename
import os
import uuid
import logging
from app import db
from models import MediaFile
from api.serializers import media_file_model, media_upload_model
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_SENDER_NAME = 'anonymous'
DEFAULT_DELETION_TIME_HOURS = 24

# Content type to data type mapping
MIME_TYPE_MAPPING = {
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'video/mp4': 'video',
    'audio/mpeg': 'audio',
    'audio/wav': 'audio',
    'application/pdf': 'document',
    'application/msword': 'document',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document'
}

ALLOWED_MIME_TYPES = {
    'image': ['image/jpeg', 'image/png', 'image/gif'],
    'video': ['video/mp4'],
    'audio': ['audio/mpeg', 'audio/wav'],
    'document': ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
}

def get_data_type_from_mime(content_type):
    """Determine data type from MIME type"""
    return MIME_TYPE_MAPPING.get(content_type, 'unknown')

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_upload(file):
    """Validate file upload including size, extension, and content type"""
    if not file:
        return False, "No file provided"
    
    if not file.filename:
        return False, "No filename provided"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    if not file.content_type:
        content_type = mimetypes.guess_type(file.filename)[0]
        if not content_type:
            return False, "Could not determine file content type"
        file.content_type = content_type
    
    # Validate content type
    valid_mime_type = False
    for mime_types in ALLOWED_MIME_TYPES.values():
        if file.content_type in mime_types:
            valid_mime_type = True
            break
    if not valid_mime_type:
        return False, f"Invalid content type: {file.content_type}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size allowed: {MAX_FILE_SIZE/1024/1024}MB"
    
    return True, None

def cleanup_file(file_path):
    """Clean up file in case of failure"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")

def register_media_routes(ns):
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    @ns.route('/')
    class MediaFileUpload(Resource):
        @ns.doc('upload_media_file',
               description='Upload a media file with metadata. All metadata fields are optional.')
        @ns.expect(media_upload_model)
        @ns.marshal_with(media_file_model, code=201)
        def post(self):
            """Upload a new media file with optional metadata"""
            try:
                if 'file' not in request.files:
                    ns.abort(400, "No file part in the request")
                
                file = request.files['file']
                # Validate file
                is_valid, error_message = validate_file_upload(file)
                if not is_valid:
                    ns.abort(400, error_message)

                data = request.form
                
                # Handle optional fields with defaults
                sender_name = data.get('sender_name', DEFAULT_SENDER_NAME)
                logger.info(f"Using sender name: {sender_name}")

                # Determine data type from content type if not provided
                data_type = data.get('data_type')
                if not data_type:
                    data_type = get_data_type_from_mime(file.content_type)
                    logger.info(f"Automatically determined data type: {data_type}")

                # Set deletion time to 24 hours from now if not provided
                try:
                    deletion_time = datetime.fromisoformat(data['deletion_time']) if 'deletion_time' in data else \
                                  datetime.utcnow() + timedelta(hours=DEFAULT_DELETION_TIME_HOURS)
                    logger.info(f"Using deletion time: {deletion_time.isoformat()}")
                except ValueError:
                    ns.abort(400, "Invalid deletion_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

                # Generate secure filename with UUID
                original_extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{original_extension}"
                file_path = os.path.join('uploads', filename)
                full_path = os.path.join(current_app.root_path, file_path)
                
                # Save the file
                try:
                    file.save(full_path)
                    logger.info(f"File saved successfully: {filename}")
                except Exception as e:
                    logger.error(f"Error saving file: {str(e)}")
                    cleanup_file(full_path)
                    ns.abort(500, f"Error saving file: {str(e)}")
                
                # Create media file record
                try:
                    media_file = MediaFile(
                        sender_name=sender_name,
                        data_type=data_type,
                        file_path=file_path,
                        deletion_time=deletion_time,
                        content_type=file.content_type
                    )
                    
                    db.session.add(media_file)
                    db.session.commit()
                    logger.info(f"Media file record created: {media_file.id}")
                    return media_file, 201
                except Exception as e:
                    logger.error(f"Database error: {str(e)}")
                    cleanup_file(full_path)
                    db.session.rollback()
                    ns.abort(500, f"Error creating media file record: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Unexpected error in file upload: {str(e)}")
                ns.abort(500, f"Unexpected error: {str(e)}")

    @ns.route('/by-type/<string:type>')
    class MediaFileByType(Resource):
        @ns.doc('get_media_by_type',
               description='Get media files filtered by type')
        @ns.marshal_list_with(media_file_model)
        def get(self, type):
            """Get media files by type"""
            try:
                return MediaFile.query.filter_by(data_type=type).all()
            except Exception as e:
                logger.error(f"Error retrieving media files by type: {str(e)}")
                ns.abort(500, f"Error retrieving media files: {str(e)}")

    @ns.route('/by-timespan')
    @ns.param('start', 'Start timestamp (ISO format)')
    @ns.param('end', 'End timestamp (ISO format)')
    class MediaFileByTimespan(Resource):
        @ns.doc('get_media_by_timespan',
               description='Get media files within a timespan')
        @ns.marshal_list_with(media_file_model)
        def get(self):
            """Get media files within a timespan"""
            try:
                start = datetime.fromisoformat(request.args.get('start', ''))
                end = datetime.fromisoformat(request.args.get('end', ''))
            except ValueError:
                ns.abort(400, "Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
            
            try:
                return MediaFile.query.filter(
                    MediaFile.timestamp.between(start, end)
                ).all()
            except Exception as e:
                logger.error(f"Error retrieving media files by timespan: {str(e)}")
                ns.abort(500, f"Error retrieving media files: {str(e)}")

def delete_expired_files():
    """Delete media files that have passed their deletion time"""
    with current_app.app_context():
        try:
            expired_files = MediaFile.query.filter(
                MediaFile.deletion_time <= datetime.utcnow()
            ).all()
            
            for media_file in expired_files:
                try:
                    # Delete the physical file
                    file_path = os.path.join(current_app.root_path, media_file.file_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Deleted expired file: {file_path}")
                    
                    # Delete the database record
                    db.session.delete(media_file)
                    logger.info(f"Deleted media file record: {media_file.id}")
                except Exception as e:
                    logger.error(f"Error deleting file {media_file.id}: {str(e)}")
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Error in delete_expired_files: {str(e)}")
            db.session.rollback()
