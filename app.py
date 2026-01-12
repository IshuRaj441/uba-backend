import os
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from extensions import db, migrate
from werkzeug.security import generate_password_hash
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from models.user import User


def create_app():
    app = Flask(__name__)
    CORS(app)

    # ---------------- CONFIG ----------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["OUTPUT_FOLDER"] = "outputs"
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret")

    # Database (Render-safe SQLite)
    db_path = os.path.join(BASE_DIR, "instance", "app.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---------------- INIT ----------------
    db.init_app(app)
    migrate.init_app(app, db)

    # ---------------- ROUTES ----------------
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    # ---------------- DATABASE BOOTSTRAP ----------------
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
            user = User(
                email="raji53681@gmail.com",
                password=generate_password_hash("test123"),
                credits=100,
                is_admin=False
            )
            db.session.add(user)

        db.session.commit()

    # ---------------- HEALTH ----------------
    app.start_time = time.time()

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "uptime": round(time.time() - app.start_time, 2)
        })

    return app


# Gunicorn entry point
app = create_app()

