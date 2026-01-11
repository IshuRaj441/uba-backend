#!/bin/bash

# Set environment variables
export FLASK_APP=wsgi:app
export FLASK_ENV=production

# Install dependencies if not already installed
python -m pip install -r requirements.txt

# Run the application using Waitress
python -m waitress --port=$PORT wsgi:app
