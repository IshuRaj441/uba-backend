import os
from app import create_app, db
from config import ProductionConfig

# Create application instance
app = create_app(ProductionConfig)

# Ensure the database tables are created
with app.app_context():
    db.create_all()

# This file is used by Gunicorn to serve the application
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
