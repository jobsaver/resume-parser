"""
Controller for resume builder functionality.
Handles theme management and resume generation.
"""
import uuid
from flask import jsonify
from rendercv_integration import resume_renderer
from database import save_resume_document
from storage import upload_file_to_spaces, generate_spaces_key
from template_manager import ThemeManager

# Initialize theme manager
theme_manager = ThemeManager()

def get_themes():
    """
    Get list of available themes
    
    Returns:
        tuple: (success, result)
    """
    try:
        themes_list = theme_manager.get_themes()
        return True, themes_list
    except Exception as e:
        return False, str(e)

def get_theme_details(theme_id):
    """
    Get detailed information about a specific theme
    
    Args:
        theme_id: Theme identifier
        
    Returns:
        tuple: (success, result)
    """
    try:
        theme = theme_manager.get_theme(theme_id)
        if not theme:
            return False, f"Theme '{theme_id}' not found"
        
        return True, theme
    except Exception as e:
        return False, str(e)

def preview_resume(theme_id, resume_data):
    """
    Generate HTML preview for resume with given theme
    
    Args:
        theme_id: Theme identifier
        resume_data: Resume content
        
    Returns:
        tuple: (success, result)
    """
    try:
        if not theme_manager.get_theme(theme_id):
            return False, f"Theme '{theme_id}' not found"
        
        # Create resume using ResumeRenderer
        success, result = resume_renderer.render_resume(resume_data, theme_id)
        
        if not success:
            return False, result.get('error', 'Unknown error creating preview')
        
        # Get the HTML content
        html_path = result.get('html_path')
        if not html_path:
            return False, 'No HTML preview generated'
            
        with open(html_path, 'r') as f:
            html_content = f.read()
            
        return True, {
            'html': html_content,
            'theme': theme_manager.get_theme(theme_id)
        }
        
    except Exception as e:
        return False, str(e)

def create_resume_with_rendercv(user_id, resume_data, theme_id='classic'):
    """
    Create a resume using RenderCV
    
    Args:
        user_id: User ID
        resume_data: Resume content
        theme_id: Theme identifier
        
    Returns:
        tuple: (success, result)
    """
    try:
        if not theme_manager.get_theme(theme_id):
            return False, f"Theme '{theme_id}' not found"
        
        # Create resume using ResumeRenderer
        success, result = resume_renderer.render_resume(resume_data, theme_id)
        
        if not success:
            return False, result.get('error', 'Unknown error creating resume')
        
        # Upload the generated PDF
        pdf_path = result['pdf_path']
        resume_id = result['resume_id']
        spaces_key = generate_spaces_key(user_id, resume_id, f"{resume_id}.pdf")
        
        upload_success, spaces_result = upload_file_to_spaces(pdf_path, spaces_key, 'application/pdf')
        
        if not upload_success:
            return False, f'Error uploading file to storage: {spaces_result}'
        
        # Store the file URL
        file_url = spaces_result
        
        # Create document
        document = {
            "resume_id": resume_id,
            "user_id": user_id,
            "content": resume_data,
            "url": file_url,
            "format": "rendercv",
            "theme": theme_id
        }
        
        # Save to database
        saved_id = save_resume_document(document)
        
        # Create response
        response_result = {
            'resume_id': saved_id,
            'user_id': user_id,
            'content': resume_data,
            'format': 'rendercv',
            'theme': theme_manager.get_theme(theme_id),
            'file_url': file_url,
            'preview_url': f'/api/resume-preview/{saved_id}',
            'download_url': f'/api/download-resume/{saved_id}'
        }
        
        return True, response_result
        
    except Exception as e:
        return False, str(e)

def create_resume_with_template(user_id, template_id, resume_data):
    """
    Create a resume using a template
    
    Args:
        user_id: User ID
        template_id: Template ID
        resume_data: Resume content
        
    Returns:
        tuple: (success, result)
    """
    try:
        # Generate resume using template
        html_content = template_manager.create_resume(template_id, resume_data)
        
        # Generate resume ID
        resume_id = str(uuid.uuid4())
        
        # Create document
        document = {
            "resume_id": resume_id,
            "user_id": user_id,
            "content": resume_data,
            "template_id": template_id,
            "format": "template",
            "html_content": html_content
        }
        
        # Save to database
        saved_id = save_resume_document(document)
        
        return True, {
            'resume_id': saved_id,
            'html': html_content
        }
        
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f'Failed to create resume: {str(e)}'

def get_template_list():
    """
    Get list of available templates
    
    Returns:
        list: Available templates
    """
    return template_manager.get_template_list()

def get_template_details(template_id):
    """
    Get template details
    
    Args:
        template_id: Template ID
        
    Returns:
        dict: Template details or None if not found
    """
    return template_manager.get_template(template_id)

def get_template_preview(template_id):
    """
    Get template preview image path
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: (success, result)
    """
    template = template_manager.get_template(template_id)
    if not template:
        return False, f'Template {template_id} not found'
    return True, template['preview_png'] 