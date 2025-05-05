"""
Resume builder controller.
Handles resume creation, preview generation, and theme management.
"""
from pathlib import Path
import json
import yaml
import tempfile
import time
from utils.converter import convert_json_to_yaml
from rendercv_integration import ResumeRenderer
from template_manager import ThemeManager

# Initialize managers
resume_renderer = ResumeRenderer()
theme_manager = ThemeManager()

def get_all_themes():
    """Get list of all available themes with previews"""
    try:
        themes = theme_manager.get_themes()
        return True, [{
            'id': theme['id'],
            'title': theme['name'],
            'preview_image': theme['preview_image']
        } for theme in themes]
    except Exception as e:
        return False, f'Error fetching themes: {str(e)}'

def get_theme_details(theme_id):
    """Get detailed template for a specific theme"""
    try:
        json_path = Path('templates/json') / f'{theme_id}.json'
        if not json_path.exists():
            return False, 'Theme not found'
            
        with open(json_path, 'r') as f:
            theme_data = json.load(f)
            
        return True, theme_data
        
    except Exception as e:
        return False, f'Error fetching theme details: {str(e)}'

def preview_resume(theme_id, json_data):
    """Generate resume preview from JSON data"""
    try:
        success, result = resume_renderer.preview_resume(json_data, theme_id)
        if success and result.get('html_path'):
            return True, {
                'html': result['html_path'],
                'theme': theme_id
            }
        return False, 'Error generating preview'
    except Exception as e:
        return False, f'Error creating preview: {str(e)}'

def create_resume_with_rendercv(user_id, json_data, theme_id):
    """Create resume PDF from JSON data"""
    try:
        success, result = resume_renderer.render_resume(json_data, theme_id)
        if success and result.get('pdf_path'):
            return True, {
                'pdf_url': result['pdf_path'],
                'preview_url': result.get('html_path'),
                'resume_id': result['resume_id']
            }
        return False, 'Error generating resume'
    except Exception as e:
        return False, f'Error creating resume: {str(e)}'