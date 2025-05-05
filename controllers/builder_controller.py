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
import rendercv_integration as rendercv
from utils.url import get_public_download_url

def get_themes():
    """Get list of available themes with their metadata"""
    try:
        themes_dir = Path('templates/json')
        themes = []
        
        for theme_file in themes_dir.glob('*.json'):
            theme_id = theme_file.stem
            with open(theme_file, 'r') as f:
                theme_data = json.load(f)
                
            # Get preview image path
            preview_path = Path('templates/png') / f'{theme_id}.png'
            preview_url = f'/api/templates/{theme_id}/preview' if preview_path.exists() else None
                
            themes.append({
                'id': theme_id,
                'name': theme_id.title(),
                'preview': preview_url,
                'design': theme_data.get('design', {})
            })
            
        return True, themes
        
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
        # Convert JSON to YAML
        yaml_data = convert_json_to_yaml(json_data)
        
        # Create temporary file for YAML
        temp_dir = Path(tempfile.gettempdir()) / "rendercv-temp"
        temp_dir.mkdir(exist_ok=True)
        
        yaml_file = temp_dir / f'resume_{int(time.time())}.yaml'
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_data, f, sort_keys=False)
            
        # Generate preview using rendercv
        preview_path = rendercv.generate_preview(yaml_file)
        if preview_path:
            preview_url = get_public_download_url(preview_path)
            return True, preview_url
        else:
            return False, 'Error generating preview'
            
    except Exception as e:
        return False, f'Error creating preview: {str(e)}'

def create_resume_with_rendercv(user_id, json_data, theme_id):
    """Create resume PDF from JSON data"""
    try:
        # Convert JSON to YAML
        yaml_data = convert_json_to_yaml(json_data)
        
        # Create temporary file for YAML
        temp_dir = Path(tempfile.gettempdir()) / "rendercv-temp"
        temp_dir.mkdir(exist_ok=True)
        
        yaml_file = temp_dir / f'resume_{user_id}_{int(time.time())}.yaml'
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_data, f, sort_keys=False)
            
        # Generate PDF using rendercv
        pdf_path = rendercv.generate_pdf(yaml_file)
        preview_path = rendercv.generate_preview(yaml_file)
        
        if pdf_path and preview_path:
            return True, {
                'pdf_url': get_public_download_url(pdf_path),
                'preview_url': get_public_download_url(preview_path)
            }
        else:
            return False, 'Error generating resume'
            
    except Exception as e:
        return False, f'Error creating resume: {str(e)}'