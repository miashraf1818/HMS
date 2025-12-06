"""
WSGI Handler for AWS Lambda
This file wraps the Django WSGI application for serverless deployment
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

# Initialize Django application
application = get_wsgi_application()

# Serverless WSGI handler (will be created by serverless-wsgi plugin)
try:
    from serverless_wsgi import handle_request
    def handler(event, context):
        return handle_request(application, event, context)
except ImportError:
    # Fallback for local development
    handler = None
