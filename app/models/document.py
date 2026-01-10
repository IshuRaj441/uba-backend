"""
Document and conversion models for the Universal Business Automation system.
"""
import os
from datetime import datetime, timezone
from app import db

class Document(db.Model):
    """Model for storing document information."""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(500), nullable=False)
    file_extension = db.Column(db.String(10))
    file_size = db.Column(db.Integer)  # Size in bytes
    file_path = db.Column(db.String(1000))  # Original file path
    converted_filename = db.Column(db.String(500))
    converted_path = db.Column(db.String(1000))  # Path to converted file
    status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, converted, failed
    
    # Metadata
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversions = db.relationship('ConversionJob', backref='document', lazy='dynamic')
    
    def get_file_size(self):
        """Return file size in a human-readable format."""
        if not self.file_size:
            return "0 B"
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    def to_dict(self):
        """Convert document data to dictionary."""
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'file_extension': self.file_extension,
            'file_size': self.file_size,
            'file_size_display': self.get_file_size(),
            'status': self.status,
            'uploaded_by': self.uploaded_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'download_url': f"/api/documents/{self.id}/download" if self.status == 'converted' else None,
            'conversions_count': self.conversions.count(),
            'last_conversion': self.conversions.order_by(ConversionJob.completed_at.desc()).first().to_dict() 
                              if self.conversions.first() else None
        }
    
    def __repr__(self):
        return f'<Document {self.original_filename} ({self.status})>'


class ConversionJob(db.Model):
    """Model for tracking document conversion jobs."""
    __tablename__ = 'conversion_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    target_format = db.Column(db.String(10), nullable=False)  # pdf, docx, jpg, etc.
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    output_path = db.Column(db.String(1000))  # Path to converted file
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert conversion job data to dictionary."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'target_format': self.target_format,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'download_url': f"/api/conversions/{self.id}/download" if self.status == 'completed' and self.output_path and os.path.exists(self.output_path) else None,
            'error_message': self.error_message
        }
    
    def __repr__(self):
        return f'<ConversionJob {self.document.original_filename} -> {self.target_format} ({self.status})>'
