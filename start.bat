@echo off
set FLASK_APP=app.py
set FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 app:app
