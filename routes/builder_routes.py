"""
Routes for resume builder functionality.
Provides endpoints for theme management and resume operations.
"""
from flask import Blueprint, request, jsonify, send_file
from controllers.builder_controller import (
    get_themes,
    get_theme_details,
    preview_resume,
    create_resume_with_rendercv,
    get_theme_preview,
    get_full_template_data,
    validate_resume_data
)
from utils.auth import authenticate_request
import json
import yaml
from pathlib import Path
import re
import os
import tempfile

# Create blueprint
builder_bp = Blueprint('builder', __name__, url_prefix='/api')

@builder_bp.route('/themes', methods=['GET'])
def list_themes():
    """Get list of available themes with their full YAML structure"""
    try:
        success, themes = get_themes()
        if success:
            themes_with_yaml = []
            for theme in themes:
                theme_id = theme['id']
                yaml_path = Path("templates/yaml") / f"{theme_id}.yaml"
                if yaml_path.exists():
                    with open(yaml_path, 'r') as f:
                        yaml_content = yaml.safe_load(f)
                        themes_with_yaml.append({
                            **theme,
                            'yaml_structure': yaml_content
                        })
                else:
                    themes_with_yaml.append(theme)

            return jsonify({
                'success': True,
                'data': {
                    'themes': themes_with_yaml,
                    'message': 'Themes retrieved successfully'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error getting themes: {themes}'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,  
            'error': str(e)
        }), 500

@builder_bp.route('/themes/<theme_id>', methods=['GET'])
def get_theme_yaml(theme_id):
    """Get full YAML content for a specific theme"""
    try:
        yaml_path = Path("templates/yaml") / f"{theme_id}.yaml"
        if not yaml_path.exists():
            return jsonify({
                'success': False,
                'error': f'Theme {theme_id} not found'
            }), 404

        with open(yaml_path, 'r') as f:
            yaml_content = f.read()
        
        return yaml_content, 200, {'Content-Type': 'application/x-yaml'}
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@builder_bp.route('/themes/<theme_id>/preview', methods=['GET'])
def get_theme_preview_image(theme_id):
    """Get preview image for a specific theme"""
    success, result = get_theme_preview(theme_id)
    
    if success:
        return send_file(result, mimetype='image/png')
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 404

@builder_bp.route('/resumes/preview', methods=['POST'])
def preview_resume_endpoint():
    """Generate preview for a resume using JSON input"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400

        resume_data = request.get_json()
        
        if not resume_data or not isinstance(resume_data, dict):
            return jsonify({
                'success': False,  
                'error': 'Invalid request body. Must be a valid JSON object.'
            }), 400

        # Validate JSON data against schema
        is_valid, error_message = validate_resume_data(resume_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Invalid resume data: {error_message}'
            }), 400

        # Get theme ID from the design section if present, otherwise use default
        theme_id = resume_data.get('design', {}).get('theme', 'classic')
        
        # Generate preview using RenderCV
        success, result = preview_resume(theme_id, resume_data)
        
        if success:
            # Get the HTML content from the HTML file
            html_file = result.get('html_path')
            pdf_file = result.get('pdf_path')
            
            if html_file and os.path.exists(html_file):
                with open(html_file, 'r') as f:
                    html_content = f.read()
                return jsonify({
                    'success': True,
                    'data': {
                        'html': html_content,
                        'theme': theme_id,
                        'resume_data': resume_data,
                        'theme_structure': result.get('theme_structure', {}),
                        'template_data': result,
                        'pdf_url': pdf_file if pdf_file and os.path.exists(pdf_file) else None
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate HTML preview'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': str(result)
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating preview: {str(e)}'
        }), 500

@builder_bp.route('/resumes/create', methods=['POST'])
@authenticate_request()
def create_resume_endpoint():
    """Create a new resume"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400

        # Get user ID from authentication
        user_id = request.user_id
        resume_data = request.get_json()
            
        if not resume_data or not isinstance(resume_data, dict):
            return jsonify({
                'success': False,
                'error': 'Invalid request body. Must be a valid JSON object.'
            }), 400

        # Validate JSON data against schema
        is_valid, error_message = validate_resume_data(resume_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Invalid resume data: {error_message}'
            }), 400

        # Get theme ID from the design section if present, otherwise use default
        theme_id = resume_data.get('design', {}).get('theme', 'classic')

        # Create resume
        success, result = create_resume_with_rendercv(user_id, resume_data, theme_id)
        
        if success:
            # Include PDF URL in response
            pdf_file = result.get('pdf_path')
            return jsonify({
                'success': True,
                'data': {
                    **result,
                    'pdf_url': pdf_file if pdf_file and os.path.exists(pdf_file) else None
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': str(result)
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error creating resume: {str(e)}'
        }), 500

@builder_bp.route('/resumes/download', methods=['POST'])
@authenticate_request()
def download_resume_endpoint():
    """Download a rendered resume from JSON data"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400

        # Get user ID from authentication
        user_id = request.user_id
        resume_data = request.get_json()
            
        if not resume_data:
            return jsonify({
                'success': False,
                'error': 'Invalid request body'
            }), 400

        # Validate JSON data against schema
        is_valid, error_message = validate_resume_data(resume_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Invalid resume data: {error_message}'
            }), 400

        # Get theme ID and format from request
        theme_id = resume_data.get('design', {}).get('theme', 'classic')
        format = request.args.get('format', 'pdf')

        # Create temporary resume
        success, result = create_resume_with_rendercv(user_id, resume_data, theme_id)
        
        if success:
            pdf_file = result.get('pdf_path')
            html_file = result.get('html_path')

            if format == 'pdf' and pdf_file and os.path.exists(pdf_file):
                # For PDF format, return URL instead of file
                pdf_url = f"/api/resumes/download/{os.path.basename(pdf_file)}"
                return jsonify({
                    'success': True,
                    'data': {
                        'pdf_url': pdf_url,
                        'file_url': pdf_url
                    }
                })
            elif format == 'html' and html_file and os.path.exists(html_file):
                # For HTML format, return the rendered HTML content
                with open(html_file, 'r') as f:
                    html_content = f.read()
                return jsonify({
                    'success': True,
                    'data': {
                        'html': html_content,
                        'pdf_url': pdf_file if pdf_file and os.path.exists(pdf_file) else None
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Failed to generate {format.upper()} file'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': str(result)
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error downloading resume: {str(e)}'
        }), 500

@builder_bp.route('/resumes/download/<filename>', methods=['GET'])
def serve_resume_file(filename):
    """Serve a generated resume file"""
    try:
        # Get the file from temp directory
        temp_dir = Path(tempfile.gettempdir()) / "rendercv-temp"
        file_path = None
        
        # Search for the file in subdirectories
        for root, dirs, files in os.walk(temp_dir):
            if filename in files:
                file_path = Path(root) / filename
                break
        
        if file_path and os.path.exists(file_path):
            return send_file(
                file_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error serving file: {str(e)}'
        }), 500

def sanitize_yaml_content(content):
    """Sanitize YAML content to handle markdown links and special characters"""
    try:
        # First pass: Try to load as is
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            # If failed, apply sanitization
            
            # Escape markdown links
            content = re.sub(r'\[(.*?)\]\((.*?)\)', r'"\[\1\](\2)"', content)
            
            # Escape special characters in text blocks
            lines = content.split('\n')
            sanitized_lines = []
            in_text_block = False
            
            for line in lines:
                # Check if line contains text that needs to be quoted
                if ':' in line and not line.strip().startswith('-'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key, value = parts
                        value = value.strip()
                        if value and not value.startswith('"') and not value.startswith("'"):
                            # Quote the value if it contains special characters
                            if any(char in value for char in '[]():#,'):
                                value = f"'{value}'"
                            line = f"{key}: {value}"
                
                sanitized_lines.append(line)
            
            sanitized_content = '\n'.join(sanitized_lines)
            return yaml.safe_load(sanitized_content)
    except Exception as e:
        raise ValueError(f"Failed to sanitize YAML content: {str(e)}")