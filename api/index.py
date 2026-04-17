import os
import sys

# Add the project root to the path so we can import 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

app = create_app()

# Vercel needs the 'app' variable to be the Flask instance
# Note: Since Vercel won't have the frontend/dist folder available 
# to the Python runtime in the same way, the Flask app's static_folder 
# logic might error out or serve nothing, but vercel.json rewrites 
# will handle serving the static files from the frontend/dist directly.
