"""
Document conversion API endpoints
"""
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from app import db
from app.models import Document, ConversionJob, ActivityLog
from modules.document_converter import DocumentConverter

# Initialize document converter
doc_converter = DocumentConverter(upload_folder=os.path.join('..', 'uploads'))

bp = Blueprint('documents', __name__, url_prefix='/api/documents')

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'tex'
    }

@bp.route('/convert', methods=['POST'])
def convert_document():
    """
    Convert a document to another format
    
    Expected form data:
    - file: The file to convert
    - target_format: The target format (pdf, docx, jpg, tex, etc.)
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    target_format = request.form.get('target_format', '').lower()
    
    # If user does not select file, browser may submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Validate target format
    valid_formats = {
        'pdf': ['docx', 'doc', 'jpg', 'jpeg', 'png', 'tex'],
        'docx': ['pdf'],
        'doc': ['pdf'],
        'jpg': ['pdf', 'docx'],
        'jpeg': ['pdf', 'docx'],
        'png': ['pdf', 'docx'],
        'tex': ['pdf']
    }
    
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    
    if file_ext not in valid_formats or target_format not in valid_formats[file_ext]:
        return jsonify({
            'error': f'Conversion from .{file_ext} to .{target_format} is not supported',
            'supported_conversions': valid_formats.get(file_ext, [])
        }), 400
    
    # Create a new document record
    document = Document(
        original_filename=secure_filename(file.filename),
        file_extension=file_ext,
        file_size=request.content_length or 0,
        status='uploaded'
    )
    db.session.add(document)
    
    # Create a conversion job
    job = ConversionJob(
        document_id=document.id,
        target_format=target_format,
        status='pending'
    )
    db.session.add(job)
    
    try:
        # Save the uploaded file
        filename = f"{uuid.uuid4()}.{file_ext}"
        upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Update document with file path
        document.file_path = filepath
        
        # Process the conversion
        output_filename = f"{uuid.uuid4()}.{target_format}"
        output_dir = os.path.join(current_app.root_path, '..', 'converted')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        
        # Determine conversion type
        conversion_type = f"{file_ext}_to_{target_format}"
        
        # Perform the conversion
        success, message = False, ""
        
        if conversion_type == 'pdf_to_docx':
            success, message = doc_converter.pdf_to_word(filepath, output_path)
        elif conversion_type in ['docx_to_pdf', 'doc_to_pdf']:
            success, message = doc_converter.word_to_pdf(filepath, output_path)
        elif conversion_type in ['jpg_to_pdf', 'jpeg_to_pdf', 'png_to_pdf']:
            success, message = doc_converter.image_to_pdf(filepath, output_path)
        elif conversion_type in ['jpg_to_docx', 'jpeg_to_docx', 'png_to_docx']:
            success, message = doc_converter.image_to_word(filepath, output_path)
        elif conversion_type == 'pdf_to_tex':
            success, message = doc_converter.pdf_to_latex(filepath, output_path)
        elif conversion_type == 'tex_to_pdf':
            success, message = doc_converter.latex_to_pdf(filepath, output_path)
        else:
            message = f"Unsupported conversion: {conversion_type}"
        
        if success:
            # Update job status
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.output_path = output_path
            
            # Update document with converted file info
            document.converted_filename = output_filename
            document.converted_path = output_path
            document.status = 'converted'
            
            # Log the activity
            activity = ActivityLog(
                action='document_conversion',
                entity_type='document',
                entity_id=document.id,
                details={
                    'original_file': document.original_filename,
                    'converted_file': output_filename,
                    'conversion_type': conversion_type
                }
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Document converted successfully',
                'document_id': document.id,
                'download_url': f"/api/documents/download/{output_filename}",
                'conversion_job_id': job.id
            })
        else:
            raise Exception(message or 'Conversion failed')
            
    except Exception as e:
        db.session.rollback()
        job.status = 'failed'
        job.error_message = str(e)
        document.status = 'error'
        db.session.commit()
        
        return jsonify({
            'status': 'error',
            'message': f'Failed to convert document: {str(e)}',
            'document_id': document.id,
            'job_id': job.id
        }), 500

@bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a converted file"""
    try:
        # Security: Only allow downloading from the converted directory
        safe_filename = secure_filename(filename)
        filepath = os.path.join(current_app.root_path, '..', 'converted', safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(
            filepath,
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a conversion job"""
    job = ConversionJob.query.get_or_404(job_id)
    
    return jsonify({
        'job_id': job.id,
        'status': job.status,
        'document_id': job.document_id,
        'target_format': job.target_format,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error_message': job.error_message
    })

@bp.route('/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get document details"""
    document = Document.query.get_or_404(document_id)
    
    return jsonify({
        'id': document.id,
        'original_filename': document.original_filename,
        'file_extension': document.file_extension,
        'file_size': document.file_size,
        'status': document.status,
        'created_at': document.created_at.isoformat() if document.created_at else None,
        'converted_filename': document.converted_filename,
        'download_url': f"/api/documents/download/{document.converted_filename}" if document.converted_filename else None
    })
