"""RenderCV integration module."""
import os
import uuid
import tempfile
from pathlib import Path
from rendercv.api import (
    create_a_pdf_from_a_python_dictionary,
    create_an_html_file_from_a_python_dictionary,
    create_a_typst_file_from_a_python_dictionary,
    create_a_markdown_file_from_a_python_dictionary
)
import yaml
import json

class ResumeRenderer:
    def __init__(self):
        """Initialize the ResumeRenderer."""
        self.temp_dir = Path(tempfile.gettempdir()) / "rendercv-temp"
        self.temp_dir.mkdir(exist_ok=True)

    def render_resume(self, resume_data, theme_id='classic'):
        """
        Render a resume using RenderCV.
        
        Args:
            resume_data: Dictionary containing resume data in JSON format
            theme_id: Theme to use for rendering
            
        Returns:
            tuple: (success, result)
        """
        try:
            # Create unique ID for this resume
            resume_id = str(uuid.uuid4())
            output_dir = self.temp_dir / resume_id / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create base filename 
            base_name = f"{resume_data['cv']['name'].replace(' ', '_')}_CV"
            base_path = output_dir / base_name

            # Generate PDF and HTML formats
            pdf_path = str(base_path) + ".pdf"
            html_path = str(base_path) + ".html"

            # Convert JSON data to YAML structure if needed
            yaml_data = resume_data if isinstance(resume_data.get('cv'), dict) else {
                'cv': resume_data,
                'design': {'theme': theme_id}
            }

            # Render formats
            create_a_pdf_from_a_python_dictionary(yaml_data, pdf_path)
            create_an_html_file_from_a_python_dictionary(yaml_data, html_path)

            result = {
                'resume_id': resume_id,
                'output_dir': str(output_dir),
                'pdf_path': pdf_path if os.path.exists(pdf_path) else None,
                'html_path': html_path if os.path.exists(html_path) else None,
                'resume_data': resume_data
            }

            return True, result
        except Exception as e:
            return False, str(e)

    def preview_resume(self, resume_data, theme_id='classic'):
        """
        Generate a preview for a resume.
        
        Args:
            resume_data: Dictionary containing resume data in JSON format
            theme_id: Theme to use for rendering
            
        Returns:
            tuple: (success, result)
        """
        try:
            # Create unique ID for this preview
            preview_id = str(uuid.uuid4())
            output_dir = self.temp_dir / preview_id / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create base filename
            base_name = f"{resume_data['cv']['name'].replace(' ', '_')}_CV"
            base_path = output_dir / base_name

            # Generate HTML for preview
            html_path = str(base_path) + ".html"

            # Convert JSON data to YAML structure if needed
            yaml_data = resume_data if isinstance(resume_data.get('cv'), dict) else {
                'cv': resume_data,
                'design': {'theme': theme_id}
            }

            # Render HTML preview
            create_an_html_file_from_a_python_dictionary(yaml_data, html_path)

            result = {
                'resume_id': preview_id,
                'output_dir': str(output_dir),
                'html_path': html_path if os.path.exists(html_path) else None,
                'resume_data': resume_data
            }

            return True, result
        except Exception as e:
            return False, str(e)