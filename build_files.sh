# Install dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt


# Collect static files (to Cloudinary or local)
echo "Collecting static files..."
python3.9 manage.py collectstatic
