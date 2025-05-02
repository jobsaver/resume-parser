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
    get_template_list,
    get_template_details,
    get_full_template_data
)
from utils.auth import authenticate_request
import json
import yaml
from pathlib import Path
import re

# Create blueprint
builder_bp = Blueprint('builder', __name__, url_prefix='/api')

@builder_bp.route('/themes', methods=['GET'])
def list_themes():
    """Get list of available themes"""
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

@builder_bp.route('/templates', methods=['GET'])
def list_templates():
    """Get list of available templates"""
    success, result = get_template_list()
    
    if success:
        return jsonify({
            'success': True,
            'data': {
                'templates': result,
                'message': 'Templates retrieved successfully'
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Error getting templates: {result}'
        }), 500

@builder_bp.route('/templates/<template_id>', methods=['GET'])
def get_template_data(template_id):
    """Get full template data for a specific template ID and return as YAML"""
    success, result = get_full_template_data(template_id)
    
    if success:
        # Return the full YAML content of the template
        return result, 200, {'Content-Type': 'application/x-yaml'}
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 404 if 'not found' in str(result).lower() else 500

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

@builder_bp.route('/resumes/preview', methods=['POST'])
def preview_resume_endpoint():
    """Generate HTML preview for a resume using YAML input"""
    try:
        if not request.data:
            return jsonify({
                'success': False,
                'error': 'No YAML data provided'
            }), 400

        # Get the raw YAML content from the request
        yaml_content = request.data.decode('utf-8')
        
        try:
            # Parse and sanitize YAML
            resume_data = sanitize_yaml_content(yaml_content)
            
            if not resume_data or not isinstance(resume_data, dict):
                return jsonify({
                    'success': False,
                    'error': 'Invalid YAML data. Must be a valid YAML object.'
                }), 400

            # Get theme ID from the design section if present, otherwise use default
            theme_id = resume_data.get('design', {}).get('theme', 'classic')
            
            # Generate preview
            success, result = preview_resume(theme_id, yaml.dump(resume_data))

            if success:
                # Return HTML content directly with proper content type
                return result['html_content'], 200, {'Content-Type': 'text/html'}
            else:
                return jsonify({
                    'success': False,
                    'error': str(result)
                }), 500

        except yaml.YAMLError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid YAML format: {str(e)}'
            }), 400
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating preview: {str(e)}'
        }), 500

@builder_bp.route('/resumes/download', methods=['POST'])
def download_resume():
    """Download a responsive PDF resume using YAML input"""
    try:
        if not request.data:
            return jsonify({
                'success': False,
                'error': 'No YAML data provided'
            }), 400

        # Get the raw YAML content from the request
        yaml_content = request.data.decode('utf-8')
        
        try:
            # Parse and sanitize YAML
            resume_data = sanitize_yaml_content(yaml_content)
            
            if not resume_data or not isinstance(resume_data, dict):
                return jsonify({
                    'success': False,
                    'error': 'Invalid YAML data. Must be a valid YAML object.'
                }), 400

            # Get theme ID from the design section if present, otherwise use default
            theme_id = resume_data.get('design', {}).get('theme', 'classic')

            # Create responsive PDF
            success, result = create_resume_with_rendercv(None, yaml.dump(resume_data), theme_id)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': str(result)
                }), 500

            # Return the responsive PDF file
            return send_file(
                result['pdf_path'],
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"resume_{theme_id}.pdf"
            )

        except yaml.YAMLError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid YAML format: {str(e)}'
            }), 400
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating PDF: {str(e)}'
        }), 500 