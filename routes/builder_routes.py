"""
Routes for resume builder functionality.
Provides endpoints for theme management and resume operations.
"""
from flask import Blueprint, request, jsonify
from controllers.builder_controller import (
    get_theme_details,
    preview_resume,
    create_resume_with_rendercv,
    get_all_themes
)
from utils.converter import convert_json_to_yaml
from pathlib import Path

# Create blueprint
builder_bp = Blueprint('builder', __name__, url_prefix='/api')

@builder_bp.route('/themes', methods=['GET'])
def list_themes():
    """Get list of available themes with previews"""
    success, themes = get_all_themes()
    if success:
        return jsonify({
            'success': True,
            'themes': themes
        })
    else:
        return jsonify({
            'success': False,
            'error': themes
        }), 500

@builder_bp.route('/template/<theme_id>', methods=['GET'])
def get_theme_template(theme_id):
    """Get JSON template for a specific theme"""
    success, theme = get_theme_details(theme_id)
    if success:
        return jsonify({
            'success': True,
            'theme': theme
        })
    else:
        return jsonify({
            'success': False,
            'error': theme
        }), 404

@builder_bp.route('/preview', methods=['POST'])
def preview_resume_template():
    """Generate resume preview from JSON template"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        theme_id = data['design']['theme']
        if not theme_id:
            return jsonify({
                'success': False,
                'error': 'No theme specified'
            }), 400
            
        success, result = preview_resume(theme_id, data)
        if success:
            return jsonify({
                'success': True,
                'preview': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@builder_bp.route('/create', methods=['POST'])
def create_resume():
    """Create resume from JSON template"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        theme_id = data['design']['theme']
        user_id = data.get('user_id', 'anonymous')
        
        if not theme_id:
            return jsonify({
                'success': False,
                'error': 'No theme specified'
            }), 400
            
        success, result = create_resume_with_rendercv(user_id, data, theme_id)
        if success:
            return jsonify({
                'success': True,
                'resume': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500