from app import create_app

# This makes the app importable as 'backend' for uWSGI
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)