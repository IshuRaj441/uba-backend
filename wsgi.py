from app import create_app, db

app = create_app()

# Import and register routes after app creation to avoid circular imports
from app.routes import init_app as init_routes
init_routes(app)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
