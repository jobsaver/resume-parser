"""
Theme manager for resume templates.
Handles theme loading, preview generation, and theme data management.
"""
import os
import yaml
from pathlib import Path
from rendercv.renderer import (
    create_a_typst_file,
    create_a_markdown_file,
    render_pngs_from_typst,
    render_an_html_from_markdown
)
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont

TEMPLATES_DIR = Path(__file__).parent / 'templates'
YAML_DIR = TEMPLATES_DIR / 'yaml'
HTML_DIR = TEMPLATES_DIR / 'html'
LATEX_DIR = TEMPLATES_DIR / 'latex'
PNG_DIR = TEMPLATES_DIR / 'png'

def ensure_template_dirs():
    """Ensure all template directories exist"""
    YAML_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)

def get_theme_yaml(theme_id: str):
    """Get theme YAML content"""
    ensure_template_dirs()
    yaml_path = YAML_DIR / f"{theme_id}.yaml"
    if not yaml_path.exists():
        with open(YAML_DIR / "resume.yaml") as f:
            yaml_content = f.read()
            # Save as the requested theme
            with open(yaml_path, 'w') as f_out:
                f_out.write(yaml_content)
    
    with open(yaml_path) as f:
        return f.read()

def get_html_template(theme_id: str):
    """Get HTML template content"""
    ensure_template_dirs()
    html_path = HTML_DIR / f"{theme_id}.html"
    if html_path.exists():
        with open(html_path) as f:
            return f.read()
    return ""

def get_latex_template(theme_id: str):
    """Get LaTeX template content"""
    ensure_template_dirs()
    latex_path = LATEX_DIR / f"{theme_id}.tex"
    if latex_path.exists():
        with open(latex_path) as f:
            return f.read()
    return ""

def get_theme_preview(theme_id: str):
    """Get theme preview image path"""
    ensure_template_dirs()
    png_path = PNG_DIR / f"{theme_id}.png"
    if png_path.exists():
        return str(png_path)
    return ""

def get_themes():
    """Get list of available themes"""
    ensure_template_dirs()
    themes = []
    for file in YAML_DIR.glob("*.yaml"):
        theme_id = file.stem
        if theme_id != "resume":  # Skip the base template
            themes.append({
                "id": theme_id,
                "name": theme_id.title(),
                "preview": get_theme_preview(theme_id)
            })
    return themes

def get_theme_details(theme_id: str):
    """Get full theme details"""
    yaml_content = get_theme_yaml(theme_id)
    try:
        theme_data = yaml.safe_load(yaml_content)
        return {
            "id": theme_id,
            "name": theme_id.title(),
            "preview": get_theme_preview(theme_id),
            "yaml": theme_data
        }
    except yaml.YAMLError:
        return None

class ThemeManager:
    def __init__(self):
        self.themes_dir = YAML_DIR
        self.preview_dir = PNG_DIR
        ensure_template_dirs()
        self.themes = self._load_themes()

    def get_theme_yaml(self, theme_id: str) -> str:
        """Get theme YAML content"""
        yaml_path = self.themes_dir / f"{theme_id}.yaml"
        if not yaml_path.exists():
            # Copy default template if theme doesn't exist
            default_yaml = self.themes_dir / "resume.yaml"
            if default_yaml.exists():
                with open(default_yaml, 'r') as f:
                    yaml_content = f.read()
                # Save as the requested theme
                with open(yaml_path, 'w') as f:
                    f.write(yaml_content)
            else:
                return ""
        
        with open(yaml_path, 'r') as f:
            return f.read()

    def _load_themes(self):
        """Load all theme configurations."""
        themes = {}
        for yaml_file in self.themes_dir.glob("*.yaml"):
            theme_id = yaml_file.stem
            with open(yaml_file, 'r') as f:
                theme_data = yaml.safe_load(f)

            # Create JSON template structure
            template_structure = self._create_template_structure(theme_data)

            themes[theme_id] = {
                'id': theme_id,
                'name': theme_data.get('design', {}).get('theme', theme_id).title(),
                'description': theme_data.get('design', {}).get('description', ''),
                'preview_image': str(self.preview_dir / f"{theme_id}.png"),
                'fields': self._extract_fields(theme_data),
                'template_structure': template_structure,
                'styles': theme_data.get('design', {}).get('styles', {})
            }

            # Generate preview if it doesn't exist
            if not os.path.exists(themes[theme_id]['preview_image']):
                self._generate_preview(theme_id, theme_data)

        return themes

    def _create_template_structure(self, theme_data):
        """Create JSON template structure from theme data"""
        # Extract structure from the theme data
        template = {
            'cv': {
                'name': '',
                'location': '',
                'email': '',
                'phone': '',
                'sections': {}
            },
            'design': {
                'theme': theme_data.get('design', {}).get('theme', 'classic'),
                'page': theme_data.get('design', {}).get('page', {})
            }
        }

        # Add sections from theme data
        if 'cv' in theme_data and 'sections' in theme_data['cv']:
            for section_name, section_data in theme_data['cv']['sections'].items():
                if isinstance(section_data, list) and section_data:
                    template['cv']['sections'][section_name] = []
                    
                    # Only process if first item is a dictionary
                    if isinstance(section_data[0], dict):
                        template['cv']['sections'][section_name].append(
                            {k: '' for k in section_data[0].keys()}
                        )
                    else:
                        # For string entries, create a simple structure
                        template['cv']['sections'][section_name].append({'content': ''})

        return template

    def _convert_to_json(self, yaml_data):
        """Convert YAML data to JSON structure"""
        try:
            # Load YAML if string
            if isinstance(yaml_data, str):
                yaml_data = yaml.safe_load(yaml_data)

            # Create base structure
            json_data = {
                'cv': {
                    'name': yaml_data.get('cv', {}).get('name', ''),
                    'location': yaml_data.get('cv', {}).get('location', ''),
                    'email': yaml_data.get('cv', {}).get('email', ''),
                    'phone': yaml_data.get('cv', {}).get('phone', ''),
                    'sections': {}
                },
                'design': yaml_data.get('design', {'theme': 'classic'})
            }

            # Convert sections
            if 'cv' in yaml_data and 'sections' in yaml_data['cv']:
                json_data['cv']['sections'] = yaml_data['cv']['sections']

            return json_data
        except Exception as e:
            raise ValueError(f"Error converting YAML to JSON: {str(e)}")

    def _convert_to_yaml(self, json_data):
        """Convert JSON structure to YAML format"""
        try:
            return yaml.dump(json_data)
        except Exception as e:
            raise ValueError(f"Error converting JSON to YAML: {str(e)}")

    def _extract_fields(self, theme_data):
        """Extract field structure from theme data."""
        fields = {
            'personal_info': [],
            'sections': {}
        }
        
        # Extract personal info fields
        personal_info_fields = [
            'name', 'title', 'email', 'phone', 'location',
            'linkedin', 'github', 'summary'
        ]
        
        for field in personal_info_fields:
            fields['personal_info'].append({
                'name': field,
                'type': 'text',
                'required': field in ['name', 'email']
            })
        
        # Define section fields
        section_fields = {
            'education': [
                {'name': 'institution', 'type': 'text', 'required': True},
                {'name': 'area', 'type': 'text', 'required': True},
                {'name': 'degree', 'type': 'text', 'required': True},
                {'name': 'start_date', 'type': 'text', 'required': True},
                {'name': 'end_date', 'type': 'text', 'required': True},
                {'name': 'gpa', 'type': 'text', 'required': False},
                {'name': 'highlights', 'type': 'list', 'required': False}
            ],
            'experience': [
                {'name': 'company', 'type': 'text', 'required': True},
                {'name': 'position', 'type': 'text', 'required': True},
                {'name': 'location', 'type': 'text', 'required': False},
                {'name': 'start_date', 'type': 'text', 'required': True},
                {'name': 'end_date', 'type': 'text', 'required': True},
                {'name': 'highlights', 'type': 'list', 'required': False}
            ],
            'projects': [
                {'name': 'name', 'type': 'text', 'required': True},
                {'name': 'description', 'type': 'text', 'required': True},
                {'name': 'highlights', 'type': 'list', 'required': False},
                {'name': 'technologies', 'type': 'list', 'required': False}
            ],
            'skills': [
                {'name': 'category', 'type': 'text', 'required': True},
                {'name': 'items', 'type': 'list', 'required': True}
            ]
        }
        
        for section_name, section_fields_list in section_fields.items():
            fields['sections'][section_name] = {
                'type': 'list',
                'fields': section_fields_list
            }
        
        return fields

    def _generate_preview(self, theme_id, theme_data):
        """Generate preview image for a theme."""
        try:
            # Create a temporary directory for rendering
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                
                # Write theme data to temporary file
                temp_yaml = temp_dir / f"{theme_id}.yaml"
                with open(temp_yaml, 'w') as f:
                    yaml.dump(theme_data, f)
                
                # Generate Typst file
                typst_file = create_a_typst_file(theme_data, temp_dir)
                
                # Generate Markdown file
                markdown_file = create_a_markdown_file(theme_data, temp_dir)
                
                # Generate HTML from Markdown
                html_file = render_an_html_from_markdown(markdown_file)
                
                # Generate PNGs from Typst
                png_files = render_pngs_from_typst(typst_file)
                
                # Use the first PNG as preview
                if png_files:
                    shutil.copy(png_files[0], self.preview_dir / f"{theme_id}.png")
                else:
                    self._create_fallback_preview(theme_id)
                
        except Exception as e:
            print(f"Error generating preview for theme {theme_id}: {str(e)}")
            self._create_fallback_preview(theme_id)

    def _create_fallback_preview(self, theme_id):
        """Create a fallback preview image when rendering fails."""
        try:
            # Create a simple preview image
            width = 800
            height = 1000
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
            except:
                font = ImageFont.load_default()
            
            # Draw theme name
            draw.text((20, 20), f"Theme: {theme_id.title()}", font=font, fill='black')
            
            # Draw sample content
            y = 80
            draw.text((20, y), "Sample Resume Preview", font=font, fill='black')
            y += 40
            draw.text((20, y), "Name: John Doe", font=font, fill='black')
            y += 30
            draw.text((20, y), "Email: john.doe@example.com", font=font, fill='black')
            y += 30
            draw.text((20, y), "Phone: +1 (555) 123-4567", font=font, fill='black')
            
            # Save the preview image
            image.save(self.preview_dir / f"{theme_id}.png")
        except Exception as e:
            print(f"Error creating fallback preview for theme {theme_id}: {str(e)}")

    def get_themes(self):
        """Get list of available themes."""
        return [{
            'id': theme['id'],
            'name': theme['name'],
            'description': theme['description'],
            'preview_image': theme['preview_image'],
            'template_structure': theme['template_structure']
        } for theme in self.themes.values()]

    def get_theme(self, theme_id):
        """Get detailed information about a specific theme."""
        return self.themes.get(theme_id)

    def get_theme_fields(self, theme_id):
        """Get field structure for a specific theme."""
        theme = self.themes.get(theme_id)
        return theme['fields'] if theme else None

    def get_full_template(self, theme_id):
        """Get the full template data for a specific theme ID"""
        theme_path = self.themes_dir / f"{theme_id}.yaml"
        if not theme_path.exists():
            return None
        with open(theme_path, 'r') as f:
            return yaml.safe_load(f)