"""
Controller for resume builder functionality.
"""
from typing import Dict, Any, Tuple, Union
import os
from pathlib import Path
import json
import yaml
from template_manager import ThemeManager
from rendercv_integration import ResumeRenderer

# Initialize managers
theme_manager = ThemeManager()
resume_renderer = ResumeRenderer()

def get_themes() -> Tuple[bool, Union[list, str]]:
    """Get list of available themes"""
    try:
        themes = theme_manager.get_themes()
        return True, themes
    except Exception as e:
        return False, str(e)

def get_theme_details(theme_id: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """Get details for a specific theme"""
    try:
        theme = theme_manager.get_theme(theme_id)
        if not theme:
            return False, f"Theme {theme_id} not found"
        return True, theme
    except Exception as e:
        return False, str(e)

def preview_resume(theme_id: str, resume_data: Dict[str, Any]) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """Generate a preview for a resume"""
    try:
        # Get theme template
        yaml_content = theme_manager.get_theme_yaml(theme_id)
        if not yaml_content:
            return False, f"Theme {theme_id} not found"

        # Load theme YAML structure
        theme_structure = yaml.safe_load(yaml_content)

        # Render resume
        success, result = resume_renderer.render_resume(resume_data, theme_id)
        if not success:
            return False, str(result)

        # Add full payload data to response
        result['theme_structure'] = theme_structure
        result['resume_data'] = resume_data

        return True, result
    except Exception as e:
        return False, str(e)

def create_resume_with_rendercv(user_id: str, resume_data: Dict[str, Any], theme_id: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """Create a new resume using RenderCV"""
    try:
        # Get theme template
        yaml_content = theme_manager.get_theme_yaml(theme_id)
        if not yaml_content:
            return False, f"Theme {theme_id} not found"

        # Render resume
        success, result = resume_renderer.render_resume(resume_data, theme_id)
        if not success:
            return False, str(result)

        # Add metadata
        result['user_id'] = user_id
        result['theme_id'] = theme_id
        result['resume_data'] = resume_data

        return True, result
    except Exception as e:
        return False, str(e)

def get_theme_preview(theme_id: str) -> Tuple[bool, Union[str, str]]:
    """Get preview image for a theme"""
    try:
        preview_path = theme_manager.get_theme_preview(theme_id)
        if not preview_path:
            return False, f"Preview for theme {theme_id} not found"
        return True, preview_path
    except Exception as e:
        return False, str(e)

def get_full_template_data(theme_id: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """Get full template data for a theme"""
    try:
        template = theme_manager.get_full_template(theme_id)
        if not template:
            return False, f"Template for theme {theme_id} not found"
        return True, template
    except Exception as e:
        return False, str(e)

def validate_resume_data(data: Dict[str, Any]) -> Tuple[bool, Union[None, str]]:
    """Validate resume data against schema"""
    try:
        # Basic structure validation
        if not isinstance(data, dict):
            return False, "Resume data must be a dictionary"

        # Check required sections
        if 'cv' not in data:
            return False, "Missing required 'cv' section"

        cv_data = data['cv']
        if not isinstance(cv_data, dict):
            return False, "'cv' section must be a dictionary"

        # Check required cv fields
        required_cv_fields = ['name', 'email']
        missing_fields = [field for field in required_cv_fields if field not in cv_data]
        if missing_fields:
            return False, f"Missing required fields in cv section: {', '.join(missing_fields)}"

        # Validate sections if present
        if 'sections' in cv_data:
            if not isinstance(cv_data['sections'], dict):
                return False, "'sections' must be a dictionary"

            # Validate each section
            for section_name, section_data in cv_data['sections'].items():
                if not isinstance(section_data, list):
                    return False, f"Section '{section_name}' must be a list"

        return True, None
    except Exception as e:
        return False, str(e)