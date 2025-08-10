#!/bin/bash
# Install dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

# Run migrations (for Neon DB)
echo "Running migrations..."
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

# Collect static files (to Cloudinary or local)
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

# Optional: Compile messages or other build steps