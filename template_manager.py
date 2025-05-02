"""
Theme manager for resume templates.
Handles theme loading, preview generation, and theme data management.
"""
import os
import yaml
from pathlib import Path
from rendercv import renderer
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont

class ThemeManager:
    def __init__(self):
        self.themes_dir = Path("templates/yaml")
        self.preview_dir = Path("templates/previews")
        self._ensure_directories()
        self.themes = self._load_themes()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.preview_dir.mkdir(parents=True, exist_ok=True)

    def _load_themes(self):
        """Load all theme configurations."""
        themes = {}
        for yaml_file in self.themes_dir.glob("*.yaml"):
            theme_id = yaml_file.stem
            with open(yaml_file, 'r') as f:
                theme_data = yaml.safe_load(f)

            # Ensure the theme data matches the expected structure
            if 'design' not in theme_data or 'cv' not in theme_data:
                print(f"Warning: Theme {theme_id} is missing required sections.")
                continue

            themes[theme_id] = {
                'id': theme_id,
                'name': theme_data.get('design', {}).get('theme', theme_id).title(),
                'description': theme_data.get('design', {}).get('description', ''),
                'preview_image': str(self.preview_dir / f"{theme_id}.png"),
                'fields': self._extract_fields(theme_data),
                'styles': theme_data.get('design', {}).get('styles', {})
            }
            
            # Generate preview if it doesn't exist
            if not os.path.exists(themes[theme_id]['preview_image']):
                self._generate_preview(theme_id, theme_data)
                
        return themes

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
                
                # Generate HTML using rendercv
                renderer.renderer(str(temp_yaml), str(temp_dir), theme=theme_id)
                
                # Convert HTML to PNG preview
                self._html_to_png(theme_id, temp_dir)
                
        except Exception as e:
            print(f"Error generating preview for theme {theme_id}: {str(e)}")

    def _html_to_png(self, theme_id, temp_dir):
        """Convert HTML preview to PNG image."""
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

    def get_themes(self):
        """Get list of available themes."""
        return [{
            'id': theme['id'],
            'name': theme['name'],
            'description': theme['description'],
            'preview_image': theme['preview_image']
        } for theme in self.themes.values()]

    def get_theme(self, theme_id):
        """Get detailed information about a specific theme."""
        return self.themes.get(theme_id)

    def get_theme_fields(self, theme_id):
        """Get field structure for a specific theme."""
        theme = self.themes.get(theme_id)
        return theme['fields'] if theme else None

    def get_full_template(self, template_id):
        """Get the full template data for a specific template ID"""
        template_path = self.themes_dir / f"{template_id}.yaml"
        if not template_path.exists():
            return None
        with open(template_path, 'r') as f:
            return yaml.safe_load(f) 