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
        
        cv_data = theme_data.get('cv', {})
        
        # Extract personal info fields
        for key in cv_data.keys():
            if key != 'sections':
                fields['personal_info'].append({
                    'name': key,
                    'type': 'text',
                    'required': key in ['name', 'email']
                })
        
        # Extract section fields
        sections = cv_data.get('sections', {})
        for section_name, section_content in sections.items():
            if isinstance(section_content, list) and len(section_content) > 0:
                sample_entry = section_content[0]
                if isinstance(sample_entry, dict):
                    fields['sections'][section_name] = {
                        'type': 'list',
                        'fields': [
                            {'name': k, 'type': 'text' if isinstance(v, str) else 'list'}
                            for k, v in sample_entry.items()
                        ]
                    }
                else:
                    # Handle simple list of strings
                    fields['sections'][section_name] = {
                        'type': 'list',
                        'fields': [{'name': 'item', 'type': 'text'}]
                    }
            elif isinstance(section_content, dict):
                # Handle dictionary sections
                fields['sections'][section_name] = {
                    'type': 'dict',
                    'fields': [
                        {'name': k, 'type': 'text' if isinstance(v, str) else 'list'}
                        for k, v in section_content.items()
                    ]
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