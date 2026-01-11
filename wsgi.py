from app import create_app

# Create the Flask app using the factory function
app = create_app()

# This file serves as the WSGI entry point for Gunicorn
if __name__ == "__main__":
    app.run()
