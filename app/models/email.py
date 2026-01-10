"""
Email models for the Universal Business Automation system.
"""
import json
from datetime import datetime, timezone
from app import db

class EmailTemplate(db.Model):
    """Model for storing email templates."""
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text)  # JSON string of available template variables
    is_default = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    emails = db.relationship('Email', backref='template', lazy='dynamic')
    
    def get_variables(self):
        """Parse variables JSON string to Python dict."""
        try:
            return json.loads(self.variables) if self.variables else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_variables(self, variables_dict):
        """Convert variables dict to JSON string."""
        self.variables = json.dumps(variables_dict) if variables_dict else None
    
    def to_dict(self):
        """Convert template data to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'body': self.body,
            'variables': self.get_variables(),
            'is_default': self.is_default,
            'created_by': self.created_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usage_count': self.emails.count()
        }
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'


class Email(db.Model):
    """Model for storing sent emails."""
    __tablename__ = 'emails'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    to_email = db.Column(db.String(200), nullable=False)
    from_email = db.Column(db.String(200))
    from_name = db.Column(db.String(200))
    status = db.Column(db.String(20), default='sent')  # sent, delivered, opened, clicked, bounced, failed
    error_message = db.Column(db.Text)
    
    # Metadata
    sent_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    opened_at = db.Column(db.DateTime)
    
    # Relationships
    logs = db.relationship('EmailLog', backref='email', lazy='dynamic')
    
    def to_dict(self):
        """Convert email data to dictionary."""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'subject': self.subject,
            'to_email': self.to_email,
            'from_email': self.from_email,
            'from_name': self.from_name,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'sent_by': self.sent_by_id,
            'error_message': self.error_message,
            'logs': [log.to_dict() for log in self.logs.all()]
        }
    
    def __repr__(self):
        return f'<Email to {self.to_email} ({self.status})>'


class EmailLog(db.Model):
    """Model for tracking email events and status changes."""
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    event_type = db.Column(db.String(50), nullable=False)  # sent, delivered, opened, clicked, bounced, etc.
    details = db.Column(db.Text)  # Additional event details as JSON
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_details(self):
        """Parse details JSON string to Python dict."""
        try:
            return json.loads(self.details) if self.details else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_details(self, details_dict):
        """Convert details dict to JSON string."""
        self.details = json.dumps(details_dict) if details_dict else None
    
    def to_dict(self):
        """Convert log data to dictionary."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'lead_id': self.lead_id,
            'event_type': self.event_type,
            'details': self.get_details(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<EmailLog {self.event_type} for email {self.email_id}>'
