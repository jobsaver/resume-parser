import os
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
import atexit
import time
import uuid

# Load environment variables
load_dotenv()

# Import parsers
from parsers.pdf_extractor import extract_text_from_pdf
from parsers.resume_parser import parse_resume
from database import init_db, close_db, validate_token, get_user_resumes, save_resume_document
from storage import upload_file_to_spaces, generate_spaces_key, delete_file_from_spaces
from rendercv_integration import create_resume_from_data, get_available_themes

app = Flask(__name__, static_folder='static')
# Configure CORS to allow all origins and methods for testing
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

# Configuration
PORT = int(os.getenv("PORT", 5002))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "resume-uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Configure maximum file size (10MB)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Initialize database connection
init_db()

# Register function to close database connection on application exit
atexit.register(close_db)

# Store resumes in memory (use a database in production)
resumes = {}

@app.route('/')
def serve_frontend():
    """Serve the frontend HTML page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/resume-maker')
@app.route('/resume-maker.html')
def serve_resume_maker():
    """Serve the resume maker HTML page"""
    return send_from_directory(app.static_folder, 'resume-maker.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Python resume parser server is running',
        'version': '1.0.0'
    })

def authenticate_request():
    """
    Authenticate the request using the token from headers, query parameters, or form data
    
    Returns:
        tuple: (user_id, token, error_response)
        If authentication fails, error_response will be a Flask response object
        Otherwise, error_response will be None
    """
    # Get authentication token from headers
    token = request.headers.get('Authorization')
    
    # If token is in the format "Bearer <token>", extract the token
    if token and token.startswith('Bearer '):
        token = token.split(' ')[1]
    
    # If token is not in headers, try to get it from query parameters
    if not token:
        token = request.args.get('token')
    
    # If token is not in query parameters, try to get it from form data
    if not token:
        token = request.form.get('token')
    
    # Get user ID from query parameters or form data
    user_id = request.args.get('user_id') or request.form.get('user_id')
    
    print(f"Auth request: user_id={user_id}, token={token[:4] if token else 'None'}...")
    
    # Validate inputs
    if not token:
        return None, None, (jsonify({
            'success': False,
            'error': 'Authentication token is required'
        }), 401)
    
    if not user_id:
        return None, None, (jsonify({
            'success': False,
            'error': 'User ID is required'
        }), 400)
    
    # Validate token for specific user
    if not validate_token(user_id, token):
        return None, None, (jsonify({
            'success': False,
            'error': 'Invalid authentication token'
        }), 401)
    
    return user_id, token, None

@app.route('/api/extract-only', methods=['POST', 'OPTIONS'])
def extract_only_endpoint():
    """Extract resume data without saving to the database and delete the file after extraction"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    # Log request details
    print("Request received at /api/extract-only:")
    print(f"Method: {request.method}")
    print(f"Form data: {list(request.form.keys())}")
    print(f"Files: {list(request.files.keys())}")
    print(f"Args: {list(request.args.keys())}")
    
    if 'resume' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['resume']
    
    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Only PDF files are supported'
        }), 400
    
    try:
        # Save the file temporarily
        temp_file_path = UPLOAD_FOLDER / file.filename
        file.save(temp_file_path)
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(temp_file_path)
        
        # Parse the resume
        parsed_data = parse_resume(temp_file_path, text_content)
        
        # Create a resume_id for consistency with save endpoint
        temp_resume_id = f"temp_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Create the response
        result = {
            'resume_id': temp_resume_id,
            'user_id': 'anonymous',
            'content': parsed_data,
            'format': 'standard',
            'file_url': '',  # No file URL since it's not saved
            'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content
        }
        
        # Remove the temporary file
        temp_file_path.unlink(missing_ok=True)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        # Log the full error
        print(f"Error parsing resume: {str(e)}")
        traceback.print_exc()
        
        # Remove the temporary file if it exists
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        
        return jsonify({
            'success': False,
            'error': f'Error parsing resume: {str(e)}'
        }), 500

@app.route('/api/save-resume', methods=['POST', 'OPTIONS'])
def save_resume_endpoint():
    """Extract resume data, save to database, and replace if same user ID exists"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    # Log request details
    print("Request received at /api/save-resume:")
    print(f"Method: {request.method}")
    print(f"Form data: {list(request.form.keys())}")
    print(f"Files: {list(request.files.keys())}")
    print(f"Args: {list(request.args.keys())}")
    
    # Authenticate request
    try:
        user_id, token, error_response = authenticate_request()
        if error_response:
            return error_response
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Authentication error: {str(e)}'
        }), 500
    
    # Auto-generate resume ID using timestamp
    resume_id = f"{user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
    # Get format from request (optional, default to standard)
    resume_format = request.form.get('format', 'standard')
    
    if 'resume' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['resume']
    
    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Only PDF files are supported'
        }), 400
    
    try:
        # Save the file temporarily
        temp_file_path = UPLOAD_FOLDER / file.filename
        file.save(temp_file_path)
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(temp_file_path)
        
        # Parse the resume
        parsed_data = parse_resume(temp_file_path, text_content)
        
        # Get user's existing resumes
        from database import get_user_resumes, delete_user_resumes
        existing_resumes = get_user_resumes(user_id)
        
        # If user already has resumes, delete them from database and storage
        if existing_resumes:
            print(f"Found existing resumes for user {user_id}. Replacing with new resume.")
            
            # Delete from DigitalOcean Spaces
            for resume in existing_resumes:
                # Extract the object key from the URL
                if resume.get('url'):
                    # The URL format is: https://storage-jobmato.blr1.digitaloceanspaces.com/resumes/user_id/resume_id.pdf
                    # We need to extract the "resumes/user_id/resume_id.pdf" part
                    url_parts = resume['url'].split('/')
                    if len(url_parts) >= 4:  # Make sure URL has enough parts
                        object_key = '/'.join(url_parts[3:])  # Skip protocol and domain
                        print(f"Deleting file from Spaces: {object_key}")
                        delete_file_from_spaces(object_key)
            
            # Delete from database
            print(f"Deleting resumes from database for user {user_id}")
            delete_user_resumes(user_id)
            
        # Upload file to DigitalOcean Spaces
        spaces_key = generate_spaces_key(user_id, resume_id, file.filename)
        upload_success, spaces_result = upload_file_to_spaces(temp_file_path, spaces_key, 'application/pdf')
        
        if not upload_success:
            return jsonify({
                'success': False,
                'error': f'Error uploading file to DigitalOcean Spaces: {spaces_result}'
            }), 500
            
        # Store the file URL
        file_url = spaces_result
        
        # Create document with simplified structure based on requirements
        document = {
            "resume_id": resume_id,
            "user_id": user_id,
            "content": parsed_data,
            "url": file_url,
            "format": resume_format
        }
        
        # Save the simplified document
        from database import save_resume_document
        saved_id = save_resume_document(document)
        
        # Create simplified response
        result = {
            'resume_id': saved_id,
            'user_id': user_id,
            'content': parsed_data,
            'format': resume_format,
            'file_url': file_url,
            'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content
        }
        
        # Remove the temporary file
        temp_file_path.unlink(missing_ok=True)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        # Log the full error
        print(f"Error processing resume: {str(e)}")
        traceback.print_exc()
        
        # Remove the temporary file if it exists
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        
        return jsonify({
            'success': False,
            'error': f'Error processing resume: {str(e)}'
        }), 500

@app.route('/api/themes', methods=['GET'])
def get_themes():
    """Get available RenderCV themes"""
    try:
        themes = get_available_themes()
        return jsonify({
            'success': True,
            'data': themes
        })
    except Exception as e:
        print(f"Error getting themes: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error getting themes: {str(e)}'
        }), 500

@app.route('/api/create-resume', methods=['POST', 'OPTIONS'])
def create_resume_endpoint():
    """Create a resume using RenderCV"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    # Log request details
    print("Request received at /api/create-resume:")
    print(f"Method: {request.method}")
    print(f"Form data: {list(request.form.keys())}")
    print(f"Files: {list(request.files.keys())}")
    print(f"Args: {list(request.args.keys())}")
    
    # Authenticate request
    try:
        user_id, token, error_response = authenticate_request()
        if error_response:
            return error_response
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Authentication error: {str(e)}'
        }), 500
    
    # Get resume data from request
    if 'resume_data' not in request.form:
        return jsonify({
            'success': False,
            'error': 'No resume data provided'
        }), 400
    
    try:
        # Parse resume data
        resume_data = json.loads(request.form['resume_data'])
        
        # Get theme from request (optional, default to classic)
        theme = request.form.get('theme', 'classic')
        
        # Create resume using RenderCV
        success, result = create_resume_from_data(resume_data, theme)
        
        if not success:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error creating resume')
            }), 500
        
        # Upload the generated PDF to DigitalOcean Spaces
        pdf_path = result['pdf_path']
        resume_id = result['resume_id']
        spaces_key = generate_spaces_key(user_id, resume_id, f"{resume_id}.pdf")
        
        upload_success, spaces_result = upload_file_to_spaces(pdf_path, spaces_key, 'application/pdf')
        
        if not upload_success:
            return jsonify({
                'success': False,
                'error': f'Error uploading file to DigitalOcean Spaces: {spaces_result}'
            }), 500
            
        # Store the file URL
        file_url = spaces_result
        
        # Create document with simplified structure
        document = {
            "resume_id": resume_id,
            "user_id": user_id,
            "content": resume_data,
            "url": file_url,
            "format": "rendercv",
            "theme": theme
        }
        
        # Save the document
        saved_id = save_resume_document(document)
        
        # Create simplified response
        response_result = {
            'resume_id': saved_id,
            'user_id': user_id,
            'content': resume_data,
            'format': 'rendercv',
            'theme': theme,
            'file_url': file_url
        }
        
        return jsonify({
            'success': True,
            'data': response_result
        })
        
    except Exception as e:
        # Log the full error
        print(f"Error creating resume: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Error creating resume: {str(e)}'
        }), 500

@app.route('/api/download-resume/<resume_id>', methods=['GET'])
def download_resume_endpoint(resume_id):
    """Download a resume PDF"""
    # Authenticate request
    try:
        user_id, token, error_response = authenticate_request()
        if error_response:
            return error_response
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Authentication error: {str(e)}'
        }), 500
    
    try:
        # Get user's resumes
        resumes = get_user_resumes(user_id)
        
        # Find the resume with the given ID
        resume = None
        for r in resumes:
            if r.get('resume_id') == resume_id:
                resume = r
                break
        
        if not resume:
            return jsonify({
                'success': False,
                'error': f'Resume with ID {resume_id} not found'
            }), 404
        
        # Get the file URL
        file_url = resume.get('url')
        
        if not file_url:
            return jsonify({
                'success': False,
                'error': f'No file URL found for resume with ID {resume_id}'
            }), 404
        
        # Download the file from DigitalOcean Spaces
        # This is a simplified version - in a real implementation, you would
        # download the file from DigitalOcean Spaces and serve it to the client
        return jsonify({
            'success': True,
            'data': {
                'file_url': file_url
            }
        })
        
    except Exception as e:
        # Log the full error
        print(f"Error downloading resume: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Error downloading resume: {str(e)}'
        }), 500

@app.route('/api/create-resume', methods=['POST'])
def api_create_resume():
    try:
        # Check if data is JSON or form data
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
            if 'resume_data' in data:
                data['resume_data'] = json.loads(data['resume_data'])
        
        resume_data = data.get('resume_data', {})
        theme = data.get('theme', 'classic')
        
        # Generate a unique ID for this resume
        resume_id = str(uuid.uuid4())
        
        # Create the resume using RenderCV
        success, result = create_resume_from_data(resume_data, theme)
        
        if success:
            # Store the resume data
            resumes[resume_id] = {
                'data': resume_data,
                'theme': theme,
                'pdf_path': result['pdf_path'],
                'yaml_path': result['yaml_path']
            }
            
            return jsonify({
                'success': True,
                'data': {
                    'resume_id': resume_id,
                    'preview_url': f'/api/resume-preview/{resume_id}',
                    'download_url': f'/api/download-resume/{resume_id}'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/resume-preview/<resume_id>', methods=['GET'])
def api_resume_preview(resume_id):
    if resume_id not in resumes:
        return jsonify({
            'success': False,
            'error': 'Resume not found'
        }), 404
    
    resume = resumes[resume_id]
    
    # Generate HTML preview
    html_preview = generate_html_preview(resume['data'], resume['theme'])
    
    return html_preview, 200, {'Content-Type': 'text/html'}

@app.route('/api/download-resume/<resume_id>', methods=['GET'])
def api_download_resume(resume_id):
    if resume_id not in resumes:
        return jsonify({
            'success': False,
            'error': 'Resume not found'
        }), 404
    
    resume = resumes[resume_id]
    pdf_path = resume['pdf_path']
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"resume_{resume_id}.pdf"
    )

@app.route('/api/themes', methods=['GET'])
def api_get_themes():
    themes = get_available_themes()
    return jsonify({
        'success': True,
        'data': {
            'themes': themes
        }
    })

def generate_html_preview(resume_data, theme):
    """Generate HTML preview of the resume"""
    # Theme-specific styles
    theme_styles = {
        'classic': """
            body { font-family: 'Times New Roman', serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
            h2 { border-bottom: 1px solid #ccc; padding-bottom: 5px; }
            .section { margin-bottom: 20px; }
            .contact-info { text-align: center; margin-bottom: 20px; }
            .item { margin-bottom: 15px; }
            .item-header { font-weight: bold; }
            .item-date { font-style: italic; color: #666; }
            .skills-list { display: flex; flex-wrap: wrap; }
            .skill-item { margin-right: 10px; }
        """,
        'modern': """
            body { font-family: 'Arial', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }
            h1 { text-align: center; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            .section { margin-bottom: 25px; background-color: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .contact-info { text-align: center; margin-bottom: 20px; color: #7f8c8d; }
            .item { margin-bottom: 15px; }
            .item-header { font-weight: bold; color: #2c3e50; }
            .item-date { font-style: italic; color: #7f8c8d; }
            .skills-list { display: flex; flex-wrap: wrap; }
            .skill-item { margin-right: 10px; background-color: #3498db; color: white; padding: 3px 8px; border-radius: 3px; margin-bottom: 5px; }
        """,
        'minimal': """
            body { font-family: 'Helvetica', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { text-align: center; font-weight: 300; }
            h2 { font-weight: 300; border-bottom: 1px solid #eee; padding-bottom: 5px; }
            .section { margin-bottom: 20px; }
            .contact-info { text-align: center; margin-bottom: 20px; color: #666; }
            .item { margin-bottom: 15px; }
            .item-header { font-weight: 500; }
            .item-date { color: #999; }
            .skills-list { display: flex; flex-wrap: wrap; }
            .skill-item { margin-right: 10px; }
        """
    }

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{resume_data.get('name', 'Resume')} - Resume</title>
        <style>
            {theme_styles.get(theme, theme_styles['classic'])}
        </style>
    </head>
    <body>
        <h1>{resume_data.get('name', '')}</h1>
        <div class="contact-info">
            {resume_data.get('email', '')} | {resume_data.get('phone', '')} | {resume_data.get('location', '')}
        </div>
    """

    # Education section
    if 'education' in resume_data and resume_data['education']:
        html += """
        <div class="section">
            <h2>Education</h2>
        """
        
        for edu in resume_data['education']:
            html += f"""
            <div class="item">
                <div class="item-header">{edu.get('school', '')}</div>
                <div class="item-date">{edu.get('start_date', '')} - {edu.get('end_date', '')}</div>
                <div>{edu.get('degree', '')} in {edu.get('field_of_study', '')}</div>
                {f"<div>GPA: {edu.get('gpa', '')}</div>" if edu.get('gpa') else ''}
                {f"<div>Courses: {', '.join(edu.get('courses', []))}</div>" if edu.get('courses') else ''}
            </div>
            """
        
        html += """</div>"""

    # Experience section
    if 'experience' in resume_data and resume_data['experience']:
        html += """
        <div class="section">
            <h2>Experience</h2>
        """
        
        for exp in resume_data['experience']:
            html += f"""
            <div class="item">
                <div class="item-header">{exp.get('company', '')}</div>
                <div class="item-date">{exp.get('start_date', '')} - {exp.get('end_date', '')}</div>
                <div>{exp.get('title', '')}</div>
            """
            
            if 'responsibilities' in exp and exp['responsibilities']:
                html += "<ul>"
                for resp in exp['responsibilities']:
                    html += f"<li>{resp}</li>"
                html += "</ul>"
            
            html += """</div>"""
        
        html += """</div>"""

    # Skills section
    if 'skills' in resume_data and resume_data['skills']:
        html += """
        <div class="section">
            <h2>Skills</h2>
            <div class="skills-list">
        """
        
        for skill in resume_data['skills']:
            html += f'<span class="skill-item">{skill}</span>'
        
        html += """
            </div>
        </div>
        """

    # Projects section
    if 'projects' in resume_data and resume_data['projects']:
        html += """
        <div class="section">
            <h2>Projects</h2>
        """
        
        for proj in resume_data['projects']:
            html += f"""
            <div class="item">
                <div class="item-header">{proj.get('name', '')}</div>
                <div>{proj.get('description', '')}</div>
                {f"<div>Technologies: {', '.join(proj.get('technologies', []))}</div>" if proj.get('technologies') else ''}
            </div>
            """
        
        html += """</div>"""

    html += """
    </body>
    </html>
    """

    return html

if __name__ == '__main__':
    print(f"Starting Python resume parser server on port {PORT}...")
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=PORT, debug=DEBUG) 