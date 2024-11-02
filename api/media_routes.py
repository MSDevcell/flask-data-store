from datetime import datetime
from flask import request, current_app
from flask_restx import Resource
from werkzeug.utils import secure_filename
import os
from app import db
from models import MediaFile
from api.serializers import media_file_model, media_upload_model
import mimetypes

def register_media_routes(ns):
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    @ns.route('/')
    class MediaFileUpload(Resource):
        @ns.doc('upload_media_file',
               description='Upload a media file with metadata')
        @ns.expect(media_upload_model)
        @ns.marshal_with(media_file_model, code=201)
        def post(self):
            """Upload a new media file"""
            if 'file' not in request.files:
                ns.abort(400, "No file provided")
            
            file = request.files['file']
            if file.filename == '':
                ns.abort(400, "No file selected")

            data = request.form
            if not all(k in data for k in ['sender_name', 'data_type', 'deletion_time']):
                ns.abort(400, "Missing required metadata fields")

            try:
                deletion_time = datetime.fromisoformat(data['deletion_time'])
            except ValueError:
                ns.abort(400, "Invalid deletion_time format. Use ISO format")

            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            
            # Save the file
            file.save(os.path.join(current_app.root_path, file_path))
            
            # Create media file record
            media_file = MediaFile(
                sender_name=data['sender_name'],
                data_type=data['data_type'],
                file_path=file_path,
                deletion_time=deletion_time,
                content_type=file.content_type or mimetypes.guess_type(filename)[0]
            )
            
            db.session.add(media_file)
            db.session.commit()
            
            return media_file, 201

    @ns.route('/by-type/<string:type>')
    class MediaFileByType(Resource):
        @ns.doc('get_media_by_type',
               description='Get media files filtered by type')
        @ns.marshal_list_with(media_file_model)
        def get(self, type):
            """Get media files by type"""
            return MediaFile.query.filter_by(data_type=type).all()

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
                ns.abort(400, "Invalid timestamp format. Use ISO format")
            
            return MediaFile.query.filter(
                MediaFile.timestamp.between(start, end)
            ).all()

# Background task to delete expired media files
def delete_expired_files():
    """Delete media files that have passed their deletion time"""
    expired_files = MediaFile.query.filter(
        MediaFile.deletion_time <= datetime.utcnow()
    ).all()
    
    for media_file in expired_files:
        try:
            # Delete the physical file
            file_path = os.path.join(current_app.root_path, media_file.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete the database record
            db.session.delete(media_file)
        except Exception as e:
            current_app.logger.error(f"Error deleting file {media_file.id}: {str(e)}")
    
    db.session.commit()
