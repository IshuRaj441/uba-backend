import os
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from extensions import db, migrate
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import subprocess
import uuid

from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from models.user import User


# ----------------------------
# Create App
# ----------------------------
def create_app():
    app = Flask(__name__)
    CORS(app)

    # ----------------------------
    # Config
    # ----------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-dev-key")
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
    app.config["OUTPUT_FOLDER"] = os.path.join(BASE_DIR, "outputs")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
    os.makedirs("instance", exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'instance/app.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ----------------------------
    # Init Extensions
    # ----------------------------
    db.init_app(app)
    migrate.init_app(app, db)

    # ----------------------------
    # Register Blueprints
    # ----------------------------
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    # ----------------------------
    # Create DB & default users
    # ----------------------------
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@example.com").first():
            admin = User(
                email="admin@example.com",
                password=generate_password_hash("admin123"),
                credits=1000,
                is_admin=True
            )
            db.session.add(admin)

        if not User.query.filter_by(email="raji53681@gmail.com").first():
            test = User(
                email="raji53681@gmail.com",
                password=generate_password_hash("test123"),
                credits=100,
                is_admin=False
            )
            db.session.add(test)

        db.session.commit()

    app.start_time = time.time()

    # ----------------------------
    # Routes
    # ----------------------------
    @app.route("/")
    def home():
        return jsonify({
            "service": "Universal Business Automation",
            "status": "running",
            "api": "/api",
            "health": "/api/health",
            "login": "/api/auth/login",
            "register": "/api/auth/register"
        })

    @app.route("/api")
    def api_root():
        return jsonify({
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "auth": "/api/auth",
                "tools": "/api/tools",
                "leads": "/api/leads",
                "convert": "/api/convert"
            }
        })

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "uptime": round(time.time() - app.start_time, 2),
            "timestamp": datetime.utcnow().isoformat()
        })

    return app


# ----------------------------
# Run locally
# ----------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
