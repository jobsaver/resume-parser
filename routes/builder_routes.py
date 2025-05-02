"""
Routes for resume builder functionality.
Provides endpoints for theme management and resume operations.
"""
from flask import Blueprint, request, jsonify, send_file
from controllers.builder_controller import (
    get_themes,
    get_theme_details,
    preview_resume,
    create_resume_with_rendercv
)
from utils.auth import authenticate_request
import json

# Create blueprint
builder_bp = Blueprint('builder', __name__, url_prefix='/api')

@builder_bp.route('/themes', methods=['GET'])
def list_themes():
    """Get list of available themes with their basic details"""
    success, result = get_themes()
    
    if success:
        return jsonify({
            'success': True,
            'data': {
                'themes': result,
                'message': 'Themes retrieved successfully'
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Error getting themes: {result}'
        }), 500

@builder_bp.route('/themes/<theme_id>', methods=['GET'])
def get_theme(theme_id):
    """Get detailed information about a specific theme"""
    success, result = get_theme_details(theme_id)
    
    if success:
        return jsonify({
            'success': True,
            'data': {
                'theme': result,
                'message': 'Theme details retrieved successfully'
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 404 if 'not found' in str(result).lower() else 500

@builder_bp.route('/resumes/preview', methods=['POST'])
def preview_resume_endpoint():
    """Generate preview for a resume with specified theme"""
    try:
        data = request.get_json()
        if not data or 'theme_id' not in data or 'resume_data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: theme_id and resume_data'
            }), 400
            
        success, result = preview_resume(data['theme_id'], data['resume_data'])
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'preview': result,
                    'message': 'Preview generated successfully'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 404 if 'not found' in str(result).lower() else 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating preview: {str(e)}'
        }), 500

@builder_bp.route('/resumes/download', methods=['POST'])
def download_resume():
    """Download a generated resume"""
    try:
        # Authenticate request
        user_id, token, error_response = authenticate_request()
        if error_response:
            return error_response

        data = request.get_json()
        if not data or 'theme_id' not in data or 'resume_data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: theme_id and resume_data'
            }), 400

        # Create resume
        success, result = create_resume_with_rendercv(user_id, data['resume_data'], data['theme_id'])
        
        if not success:
            return jsonify({
                'success': False,
                'error': result
            }), 500

        # Return the PDF file
        return send_file(
            result['pdf_path'],
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"resume_{user_id}.pdf"
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error downloading resume: {str(e)}'
        }), 500 