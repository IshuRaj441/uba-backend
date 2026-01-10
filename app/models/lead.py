"""
Lead and related models for the Universal Business Automation system.
"""
from datetime import datetime, timezone
from app import db

class Lead(db.Model):
    """Lead model for storing potential customer information."""
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), index=True)
    phone = db.Column(db.String(50), index=True)
    company = db.Column(db.String(200))
    position = db.Column(db.String(200))
    source = db.Column(db.String(200), index=True)
    status = db.Column(db.String(50), default='new', index=True)  # new, contacted, qualified, converted, unqualified
    notes = db.Column(db.Text)
    
    # Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    emails = db.relationship('EmailLog', backref='lead', lazy='dynamic')
    activities = db.relationship('ActivityLog', backref='lead', lazy='dynamic')
    
    def to_dict(self):
        """Convert lead data to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'position': self.position,
            'source': self.source,
            'status': self.status,
            'notes': self.notes,
            'created_by': self.created_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'emails_count': self.emails.count(),
            'last_contact': self.emails.order_by(EmailLog.sent_at.desc()).first().sent_at.isoformat() 
                            if self.emails.first() else None
        }
    
    def __repr__(self):
        return f'<Lead {self.name} ({self.email})>'


class ScrapeJob(db.Model):
    """Model for tracking lead scraping jobs."""
    __tablename__ = 'scrape_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    result_count = db.Column(db.Integer, default=0)
    error = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    leads = db.relationship('Lead', backref='scrape_job', lazy='dynamic')
    
    def to_dict(self):
        """Convert scrape job data to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'status': self.status,
            'result_count': self.result_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'leads_count': self.leads.count()
        }
    
    def __repr__(self):
        return f'<ScrapeJob {self.url} ({self.status})>'


class ExportJob(db.Model):
    """Model for tracking export jobs."""
    __tablename__ = 'export_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    export_type = db.Column(db.String(20), nullable=False)  # csv, pdf, excel, sheets
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    file_path = db.Column(db.String(500))
    error = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        """Convert export job data to dictionary."""
        return {
            'id': self.id,
            'export_type': self.export_type,
            'status': self.status,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_by': self.created_by_id,
            'download_url': f"/api/exports/{self.id}/download" if self.file_path and self.status == 'completed' else None
        }
    
    def __repr__(self):
        return f'<ExportJob {self.export_type} ({self.status})>'

# Add foreign key to Lead model after ExportJob is defined
Lead.scrape_job_id = db.Column(db.Integer, db.ForeignKey('scrape_jobs.id'))
