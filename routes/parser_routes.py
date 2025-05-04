"""
Routes for resume parsing functionality.
"""
from flask import Blueprint, request, jsonify, send_file
from controllers.parser_controller import extract_resume, save_resume, download_resume
import os

# Create blueprint
parser_bp = Blueprint('parser', __name__, url_prefix='/api')

@parser_bp.route('/extract-only', methods=['POST', 'OPTIONS'])
def extract_only_endpoint():
    """Extract resume data without saving"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
    if 'resume' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['resume']
    
    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Only PDF files are supported'
        }), 400
    
    success, result = extract_resume(file)
    
    if success:
        return jsonify({
            'success': True,
            'data': result
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Error parsing resume: {result}'
        }), 500

@parser_bp.route('/save-resume', methods=['POST', 'OPTIONS'])
def save_resume_endpoint():
    """Extract and save resume data"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
    # Get user_id from request or use 'anonymous'
    user_id = request.form.get('user_id', 'anonymous')
    resume_format = request.form.get('format', 'standard')
    
    if 'resume' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['resume']
    
    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Only PDF files are supported'
        }), 400
    
    success, result = save_resume(file, user_id, resume_format)
    
    if success:
        return jsonify({
            'success': True,
            'data': result
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Error processing resume: {result}'
        }), 500

@parser_bp.route('/download-resume/<resume_id>', methods=['GET'])
def download_resume_endpoint(resume_id):
    """Get resume PDF URL"""
    # Get user ID from request
    user_id = request.args.get('user_id', 'anonymous')
    
    success, result = download_resume(user_id, resume_id)
    
    if success:
        # Always return URL response instead of sending file
        return jsonify({
            'success': True,
            'data': result
        })
    else:
        return jsonify({
            'success': False,
            'error': str(result)
        }), 404