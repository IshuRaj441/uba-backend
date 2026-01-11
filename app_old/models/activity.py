"""
Activity logging model for the Universal Business Automation system.
"""
import json
from datetime import datetime
from ..extensions import db

class ActivityLog(db.Model):
    """
    Model for tracking user activities and system events.
    """
    __tablename__ = 'activity_logs'
    
    # Activity types
    ACTIVITY_TYPES = [
        'login', 'logout', 'login_failed',
        'document_upload', 'document_download', 'document_delete', 'document_convert',
        'lead_create', 'lead_update', 'lead_delete', 'lead_import', 'lead_export',
        'email_send', 'email_template_create', 'email_template_update', 'email_template_delete',
        'user_create', 'user_update', 'user_delete', 'user_password_change',
        'settings_update', 'system_event'
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Null for system events
    action = db.Column(db.String(50), nullable=False)  # One of ACTIVITY_TYPES
    entity_type = db.Column(db.String(50))  # e.g., 'document', 'lead', 'user', etc.
    entity_id = db.Column(db.Integer)  # ID of the affected entity
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    details = db.Column(db.Text)  # JSON string with additional details
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    # user relationship is defined in User model
    
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
        """Convert activity log to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.get_details(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def log_activity(cls, action, user_id=None, entity_type=None, entity_id=None, 
                    ip_address=None, user_agent=None, **details):
        """
        Helper method to log an activity.
        
        Args:
            action: The type of activity (must be one of ACTIVITY_TYPES)
            user_id: ID of the user who performed the action (None for system events)
            entity_type: Type of entity affected (e.g., 'document', 'lead')
            entity_id: ID of the entity affected
            ip_address: IP address of the user
            user_agent: User agent string
            **details: Additional details to store as JSON
            
        Returns:
            The created ActivityLog instance
        """
        if action not in cls.ACTIVITY_TYPES:
            action = 'system_event'
            details['original_action'] = action
        
        activity = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details) if details else None
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return activity
    
    def __repr__(self):
        return f'<ActivityLog {self.action} by user {self.user_id} on {self.entity_type} {self.entity_id}>'
