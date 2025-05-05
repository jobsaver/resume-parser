"""Converter utilities for resume formats."""
import yaml
from pathlib import Path

def get_theme_defaults(theme_id):
    """Get default design settings for a theme"""
    theme_defaults = {
        'modern': {
            'page': {
                'size': 'us-letter',
                'margins': '1.8cm',
                'show_page_numbering': False,
                'show_last_updated_date': True
            },
            'text': {
                'font_family': 'Roboto',
                'font_size': '11pt',
                'leading': '0.65em',
                'alignment': 'left'
            },
            'header': {
                'name_font_size': '32pt',
                'name_bold': True,
                'use_icons_for_connections': True,
                'alignment': 'left'
            },
            'section_titles': {
                'type': 'modern-underline',
                'font_size': '1.3em',
                'bold': True,
                'small_caps': False,
                'margin_top': '0.8cm',
                'margin_bottom': '0.4cm'
            },
            'entries': {
                'date_format': 'short',
                'use_bullet_points': True,
                'bullet_style': 'solid-circle'
            }
        },
        'professional': {
            'page': {
                'size': 'us-letter',
                'margins': '2cm',
                'show_page_numbering': True,
                'show_last_updated_date': True
            },
            'text': {
                'font_family': 'Calibri',
                'font_size': '11pt',
                'leading': '0.7em',
                'alignment': 'justified'
            },
            'header': {
                'name_font_size': '28pt',
                'name_bold': True,
                'use_icons_for_connections': False,
                'alignment': 'center',
                'style': 'minimal'
            },
            'section_titles': {
                'type': 'classic-line',
                'font_size': '1.2em',
                'bold': True,
                'small_caps': True,
                'margin_top': '0.7cm',
                'margin_bottom': '0.3cm'
            },
            'entries': {
                'date_format': 'long',
                'use_bullet_points': True,
                'bullet_style': 'diamond'
            }
        },
        'classic': {
            'page': {
                'size': 'us-letter',
                'margins': '2.2cm',
                'show_page_numbering': False,
                'show_last_updated_date': False
            },
            'text': {
                'font_family': 'Times New Roman',
                'font_size': '11pt',
                'leading': '0.75em',
                'alignment': 'left'
            },
            'header': {
                'name_font_size': '24pt',
                'name_bold': True,
                'use_icons_for_connections': False,
                'alignment': 'center'
            },
            'section_titles': {
                'type': 'classic',
                'font_size': '1.2em',
                'bold': True,
                'small_caps': True,
                'margin_top': '0.6cm',
                'margin_bottom': '0.3cm'
            },
            'entries': {
                'date_format': 'long',
                'use_bullet_points': True,
                'bullet_style': 'solid-circle'
            }
        }
    }
    return theme_defaults.get(theme_id, theme_defaults['classic'])

def convert_json_to_yaml(json_data):
    """
    Convert JSON resume data to YAML format.
    
    Args:
        json_data (dict): Resume data in JSON format
        
    Returns:
        dict: Resume data in YAML format
    """
    # Create the YAML structure
    yaml_data = {
        'cv': {
            'name': json_data['personalInfo']['name'],
            'location': json_data['personalInfo'].get('location', ''),
            'email': json_data['personalInfo']['email'],
            'phone': json_data['personalInfo'].get('phone', ''),
            'website': json_data['personalInfo'].get('website', ''),
            'social_networks': [
                {
                    'network': s['network'],
                    'username': s['username']
                }
                for s in json_data['personalInfo'].get('socialNetworks', [])
            ],
            'sections': {}
        }
    }
    
    # Convert sections
    sections = json_data['sections']
    yaml_sections = yaml_data['cv']['sections']
    
    # Handle summary/profile section
    if 'summary' in sections:
        yaml_sections['summary'] = sections['summary']
    elif 'profile' in sections:
        yaml_sections['profile'] = sections['profile']
        
    # Handle experience section
    experience_key = next((k for k in sections if k in ['experience', 'professional_experience']), None)
    if experience_key:
        yaml_sections['experience'] = [
            {
                'company': exp['company'],
                'position': exp['position'],
                'date': None,
                'start_date': exp['startDate'],
                'end_date': exp['endDate'],
                'location': exp.get('location', ''),
                'summary': exp.get('summary', ''),
                'highlights': exp.get('highlights', [])
            }
            for exp in sections[experience_key]
        ]
        
    # Handle education section
    if 'education' in sections:
        yaml_sections['education'] = [
            {
                'institution': edu['institution'],
                'area': edu.get('area', ''),
                'degree': edu['degree'],
                'start_date': edu.get('startDate', ''),
                'end_date': edu.get('endDate', ''),
                'location': edu.get('location', ''),
                'summary': edu.get('summary', ''),
                'highlights': edu.get('highlights', [])
            }
            for edu in sections['education']
        ]
        
    # Handle skills section
    skills_key = next((k for k in sections if k in ['skills', 'technical_skills']), None)
    if skills_key:
        yaml_sections['skills'] = [
            {
                'label': skill['label'],
                'details': skill['details']
            }
            for skill in sections[skills_key]
        ]
        
    # Handle certifications section
    if 'certifications' in sections:
        yaml_sections['certifications'] = [
            {
                'name': cert['name'],
                'date': cert.get('date', ''),
                'issuer': cert.get('issuer', '')
            }
            for cert in sections['certifications']
        ]
        
    # Handle projects section
    if 'projects' in sections:
        yaml_sections['projects'] = [
            {
                'name': proj['name'],
                'date': None,
                'start_date': proj.get('startDate', ''),
                'end_date': proj.get('endDate', ''),
                'summary': proj.get('summary', ''),
                'highlights': proj.get('highlights', [])
            }
            for proj in sections['projects']
        ]
        
    # Handle achievements section if present
    if 'achievements' in sections:
        yaml_sections['achievements'] = sections['achievements']

    # Get theme and its default settings
    theme_id = json_data['design']['theme']
    theme_defaults = get_theme_defaults(theme_id)
    design = json_data['design']
    
    # Add design settings with theme-specific defaults
    yaml_data['design'] = {
        'theme': theme_id,
        'page': theme_defaults['page'],
        'colors': {
            'text': design['colors'].get('text', 'rgb(51, 51, 51)'),
            'name': design['colors'].get('primary', 'rgb(0, 66, 99)'),
            'section_titles': design['colors'].get('primary', 'rgb(0, 66, 99)'),
            'links': design['colors'].get('secondary', 'rgb(0, 102, 153)'),
            'highlights': design['colors'].get('secondary', 'rgb(0, 102, 153)')
        },
        'text': {
            'font_family': design['fonts'].get('main', theme_defaults['text']['font_family']),
            'font_size': theme_defaults['text']['font_size'],
            'leading': design['spacing'].get('lineHeight', theme_defaults['text']['leading']),
            'alignment': theme_defaults['text']['alignment']
        },
        'header': theme_defaults['header'],
        'section_titles': theme_defaults['section_titles'],
        'entries': theme_defaults['entries']
    }

    # Update page margins from design if provided
    if 'spacing' in design and 'margin' in design['spacing']:
        yaml_data['design']['page']['margins'] = design['spacing']['margin']

    # Add locale settings
    yaml_data['locale'] = {
        'language': 'en',
        'date_format': theme_defaults['entries']['date_format'] == 'long' and 'MMMM YYYY' or 'MMM YYYY',
        'present': theme_defaults['entries']['date_format'] == 'long' and 'Present' or 'present'
    }

    # Add rendercv settings
    yaml_data['rendercv_settings'] = {
        'date': '2025-03-01',
        'bold_keywords': []
    }

    return yaml_data