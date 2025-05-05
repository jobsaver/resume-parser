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
from utils.converter import convert_json_to_yaml
from pathlib import Path
import json
import yaml

# Create blueprint
builder_bp = Blueprint('builder', __name__, url_prefix='/api')

@builder_bp.route('/themes', methods=['GET'])
def list_themes():
    """Get list of available themes"""
    success, themes = get_themes()
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

@builder_bp.route('/themes/<theme_id>', methods=['GET'])
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
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        # Get theme ID
        theme_id = data['design']['theme']
        if not theme_id:
            return jsonify({
                'success': False,
                'error': 'No theme specified'
            }), 400
            
        # Generate preview
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
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        # Get theme ID and user ID
        theme_id = data['design']['theme']
        user_id = data.get('user_id', 'anonymous')
        
        if not theme_id:
            return jsonify({
                'success': False,
                'error': 'No theme specified'
            }), 400
            
        # Create resume
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

@builder_bp.route('/templates/<template_id>/preview', methods=['GET'])
def get_template_preview(template_id):
    """Get preview image for a template"""
    try:
        preview_path = Path('templates/png') / f'{template_id}.png'
        if preview_path.exists():
            return send_file(preview_path, mimetype='image/png')
        else:
            return jsonify({
                'success': False,
                'error': 'Preview not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500