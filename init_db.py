from app import create_app
from app.models import *  # This will import all models after db is initialized

def init_db():
    app = create_app()
    with app.app_context():
        # Create all database tables
        from app import db
        db.create_all()
        print("Database tables created successfully!")
        print(f"Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    init_db()
