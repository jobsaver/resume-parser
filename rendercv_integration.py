"""
RenderCV integration module for resume rendering.
This module provides functionality to render resumes using RenderCV.
"""
import os
import json
import tempfile
from pathlib import Path
import uuid
from rendercv.renderer import (
    create_a_typst_file,
    create_a_markdown_file,
    render_pngs_from_typst,
    render_an_html_from_markdown
)
from rendercv.data.models import RenderCVDataModel
import yaml
from typing import Union, Dict, Any

class ResumeRenderer:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "rendercv-temp"
        self.temp_dir.mkdir(exist_ok=True)

    def render_resume(self, resume_data: Union[str, Dict[str, Any]], theme_id: str = 'classic'):
        """
        Render a resume using RenderCV
        
        Args:
            resume_data (Union[str, dict]): Resume data in YAML format or dictionary to render
            theme_id (str): Theme identifier
            
        Returns:
            tuple: (success, result)
                - success (bool): Whether the operation was successful
                - result (dict): Result data or error message
        """
        try:
            # Convert YAML resume_data to dictionary if it's a string
            resume_data_dict = yaml.safe_load(resume_data) if isinstance(resume_data, str) else resume_data

            # Validate resume_data structure
            if 'cv' not in resume_data_dict:
                return False, {'error': 'Invalid resume_data structure: missing cv section'}

            # Create a unique ID for this resume
            resume_id = str(uuid.uuid4())
            
            # Create a temporary directory for this resume
            resume_dir = self.temp_dir / resume_id
            resume_dir.mkdir(exist_ok=True)
            
            # Create a YAML file for RenderCV
            yaml_file = resume_dir / "resume.yaml"
            
            # Convert resume data to RenderCV format
            rendercv_data = self._convert_to_rendercv_format(resume_data_dict, theme_id)
            
            # Ensure rendercv_data is an instance of RenderCVDataModel
            rendercv_data_model = RenderCVDataModel(**rendercv_data)
            
            # Write the YAML file
            with open(yaml_file, "w") as f:
                yaml.dump(rendercv_data, f)
            
            # Create output directory
            output_dir = resume_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Generate Typst file
            typst_file = create_a_typst_file(rendercv_data_model, output_dir)
            
            # Generate Markdown file
            markdown_file = create_a_markdown_file(rendercv_data_model, output_dir)
            
            # Generate HTML from Markdown
            html_file = render_an_html_from_markdown(markdown_file)
            
            # Generate PNGs from Typst
            png_files = render_pngs_from_typst(typst_file)
            
            # Return the result
            return True, {
                "resume_id": resume_id,
                "typst_path": str(typst_file),
                "markdown_path": str(markdown_file),
                "html_path": str(html_file),
                "png_paths": [str(png) for png in png_files],
                "yaml_path": str(yaml_file),
                "output_dir": str(output_dir)
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, {"error": str(e)}

    def _convert_to_rendercv_format(self, resume_data: Dict[str, Any], theme_id: str) -> Dict[str, Any]:
        """
        Convert resume data to RenderCV format
        
        Args:
            resume_data (dict): Resume data to convert
            theme_id (str): Theme identifier
            
        Returns:
            dict: RenderCV data model
        """
        # Extract basic information from cv section
        cv_data = resume_data.get("cv", {})
        name = cv_data.get("name", "Unknown")
        email = cv_data.get("email", "")
        phone = cv_data.get("phone", "")
        location = cv_data.get("location", "")
        website = cv_data.get("website", "")
        social_networks = cv_data.get("social_networks", [])
        
        # Create a basic RenderCV data model
        rendercv_data = {
            "design": resume_data.get("design", {"theme": theme_id}),
            "cv": {
                "name": name,
                "email": email,
                "phone": phone,
                "location": location,
                "website": website,
                "social_networks": social_networks,
                "sections": {}
            }
        }
        
        # Add sections from cv.sections
        sections = cv_data.get("sections", {})
        for section_name, section_data in sections.items():
            if isinstance(section_data, list):
                rendercv_data["cv"]["sections"][section_name] = section_data
        
        return rendercv_data

# Create a global instance
resume_renderer = ResumeRenderer()