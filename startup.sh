#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting Gunicorn server..."
exec gunicorn --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    app.main:app