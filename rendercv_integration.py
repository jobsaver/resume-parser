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
from typing import Union

class ResumeRenderer:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "rendercv-temp"
        self.temp_dir.mkdir(exist_ok=True)

    def render_resume(self, resume_data, template_id):
        """
        Render a resume using RenderCV
        
        Args:
            resume_data (Union[str, dict]): Resume data in YAML format or dictionary to render
            template_id (str): Template identifier
            
        Returns:
            tuple: (success, result)
                - success (bool): Whether the operation was successful
                - result (dict): Result data or error message
        """
        try:
            # Convert YAML resume_data to dictionary if it's a string
            resume_data_dict = yaml.safe_load(resume_data) if isinstance(resume_data, str) else resume_data

            # Validate resume_data structure
            if 'cv' not in resume_data_dict or 'design' not in resume_data_dict:
                return False, {'error': 'Invalid resume_data structure'}

            # Create a unique ID for this resume
            resume_id = str(uuid.uuid4())
            
            # Create a temporary directory for this resume
            resume_dir = self.temp_dir / resume_id
            resume_dir.mkdir(exist_ok=True)
            
            # Create a YAML file for RenderCV
            yaml_file = resume_dir / "resume.yaml"
            
            # Convert resume data to RenderCV format
            rendercv_data = self._convert_to_rendercv_format(resume_data_dict, template_id)
            
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

    def _convert_to_rendercv_format(self, resume_data, theme_id):
        """
        Convert resume data to RenderCV format
        
        Args:
            resume_data (dict): Resume data to convert
            theme_id (str): Theme identifier
            
        Returns:
            dict: RenderCV data model
        """
        # Extract basic information
        name = resume_data.get("name", "Unknown")
        email = resume_data.get("email", "")
        phone = resume_data.get("phone", "")
        location = resume_data.get("location", "")
        
        # Create a basic RenderCV data model
        rendercv_data = {
            "design": {
                "theme": theme_id
            },
            "cv": {
                "name": name,
                "email": email,
                "phone": phone,
                "location": location,
                "sections": {}
            }
        }
        
        # Add education section if available
        if "education" in resume_data and resume_data["education"]:
            education_entries = []
            for edu in resume_data["education"]:
                education_entry = {
                    "institution": edu.get("school", ""),
                    "area": edu.get("degree", ""),
                    "degree": edu.get("field_of_study", ""),
                    "start_date": edu.get("start_date", ""),
                    "end_date": edu.get("end_date", ""),
                    "highlights": []
                }
                
                # Add GPA if available
                if "gpa" in edu:
                    education_entry["highlights"].append(f"GPA: {edu['gpa']}")
                    
                # Add coursework if available
                if "courses" in edu and edu["courses"]:
                    courses = ", ".join(edu["courses"])
                    education_entry["highlights"].append(f"Coursework: {courses}")
                    
                education_entries.append(education_entry)
                
            rendercv_data["cv"]["sections"]["education"] = education_entries
        
        # Add experience section if available
        if "experience" in resume_data and resume_data["experience"]:
            experience_entries = []
            for exp in resume_data["experience"]:
                experience_entry = {
                    "company": exp.get("company", ""),
                    "position": exp.get("title", ""),
                    "start_date": exp.get("start_date", ""),
                    "end_date": exp.get("end_date", ""),
                    "highlights": []
                }
                
                # Add responsibilities if available
                if "responsibilities" in exp and exp["responsibilities"]:
                    for resp in exp["responsibilities"]:
                        experience_entry["highlights"].append(resp)
                        
                experience_entries.append(experience_entry)
                
            rendercv_data["cv"]["sections"]["experience"] = experience_entries
        
        # Add skills section if available
        if "skills" in resume_data and resume_data["skills"]:
            skills_entries = []
            for skill in resume_data["skills"]:
                if isinstance(skill, dict):
                    skills_entries.append(skill)
                else:
                    skills_entries.append({"name": skill})
                    
            rendercv_data["cv"]["sections"]["skills"] = skills_entries
        
        # Add projects section if available
        if "projects" in resume_data and resume_data["projects"]:
            project_entries = []
            for project in resume_data["projects"]:
                project_entry = {
                    "name": project.get("name", ""),
                    "description": project.get("description", ""),
                    "highlights": []
                }
                
                # Add technologies if available
                if "technologies" in project and project["technologies"]:
                    techs = ", ".join(project["technologies"])
                    project_entry["highlights"].append(f"Technologies: {techs}")
                    
                project_entries.append(project_entry)
                
            rendercv_data["cv"]["sections"]["projects"] = project_entries
        
        return rendercv_data

# Create a global instance
resume_renderer = ResumeRenderer() 