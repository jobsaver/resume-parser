"""
Authentication utilities for the resume parser application.
"""
from functools import wraps
from flask import request, jsonify
import os

def authenticate_request():
    """
    Decorator to authenticate API requests using token-based authentication.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({
                    'success': False,
                    'error': 'No authorization token provided'
                }), 401

            # Extract token from Bearer format
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid authorization header format'
                }), 401

            # Check if token exists in environment variables
            user_id = None
            for key, value in os.environ.items():
                if key.startswith('TOKEN_') and value == token:
                    user_id = key.replace('TOKEN_', '')
                    break

            if not user_id:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired token'
                }), 401

            # Add user_id to request context
            request.user_id = user_id
            return f(*args, **kwargs)
        return decorated_function
    return decorator 