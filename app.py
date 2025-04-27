import os
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
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
from database import init_db, close_db, validate_token, get_user_resumes
from storage import upload_file_to_spaces, generate_spaces_key

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

@app.route('/')
def serve_frontend():
    """Serve the frontend HTML page"""
    return send_from_directory(app.static_folder, 'index.html')

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
        
        # Create the response
        result = {
            'parsedData': parsed_data,
            'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content,
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
        existing_resumes = get_user_resumes(user_id)
        
        # If user already has resumes, delete them (replace with new one)
        if existing_resumes:
            from database import delete_user_resumes
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
            'file_url': file_url
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

if __name__ == '__main__':
    print(f"Starting Python resume parser server on port {PORT}...")
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=PORT, debug=DEBUG) 