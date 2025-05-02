"""
Authentication utility functions.
"""
from flask import request, jsonify
from database import validate_token

def authenticate_request():
    """
    Authenticate the request using the token from headers, query parameters, or form data
    
    Returns:
        tuple: (user_id, token, error_response)
        If authentication fails, error_response will be a Flask response object
        Otherwise, error_response will be None
    """
    # Get authentication token from headers
    token = request.headers.get('Authorization')
    
    # If token is in the format "Bearer <token>", extract the token
    if token and token.startswith('Bearer '):
        token = token.split(' ')[1]
    
    # If token is not in headers, try to get it from query parameters
    if not token:
        token = request.args.get('token')
    
    # If token is not in query parameters, try to get it from form data
    if not token:
        token = request.form.get('token')
    
    # Get user ID from query parameters or form data
    user_id = request.args.get('user_id') or request.form.get('user_id')
    
    print(f"Auth request: user_id={user_id}, token={token[:4] if token else 'None'}...")
    
    # Validate inputs
    if not token:
        return None, None, (jsonify({
            'success': False,
            'error': 'Authentication token is required'
        }), 401)
    
    if not user_id:
        return None, None, (jsonify({
            'success': False,
            'error': 'User ID is required'
        }), 400)
    
    # Validate token for specific user
    if not validate_token(user_id, token):
        return None, None, (jsonify({
            'success': False,
            'error': 'Invalid authentication token'
        }), 401)
    
    return user_id, token, None 