#!/usr/bin/env sh
set -e

# Ensure database exists and is up-to-date
flask db upgrade || flask initdb

# Seed sample questions if none exist
flask seed || true

# Run the app listening on all interfaces
exec flask run --host=0.0.0.0 --port=5000
