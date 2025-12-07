#!/usr/bin/env sh
set -e

# Ensure database exists and is up-to-date
flask db upgrade || flask initdb

# Seed sample questions if none exist
flask seed || true

# Run the app based on environment
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting in DEVELOPMENT mode with Flask development server..."
    exec flask run --host=0.0.0.0 --port=5000
else
    echo "Starting in PRODUCTION mode with Waitress..."
    exec python production_server.py
fi