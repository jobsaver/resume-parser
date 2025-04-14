import os
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
import atexit

# Load environment variables
load_dotenv()

# Import parsers
from parsers.pdf_extractor import extract_text_from_pdf
from parsers.resume_parser import parse_resume
from database import init_db, close_db, save_parsed_resume, get_resume, get_user_resumes, validate_token

app = Flask(__name__, static_folder='static')
CORS(app)

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
    Authenticate the request using the token from headers or query parameters
    
    Returns:
        tuple: (user_id, token, error_response)
        If authentication fails, error_response will be a Flask response object
        Otherwise, error_response will be None
    """
    # Get authentication token and user ID from request
    token = request.headers.get('Authorization')
    
    # If token is in the format "Bearer <token>", extract the token
    if token and token.startswith('Bearer '):
        token = token.split(' ')[1]
    
    # If token is not in headers, try to get it from query parameters
    if not token:
        token = request.args.get('token')
    
    # Get user ID from query parameters
    user_id = request.args.get('user_id')
    
    # Validate inputs
    if not token:
        return None, None, jsonify({
            'success': False,
            'error': 'Authentication token is required'
        }), 401
    
    if not user_id:
        return None, None, jsonify({
            'success': False,
            'error': 'User ID is required'
        }), 400
    
    # Validate token
    if not validate_token(token):
        return None, None, jsonify({
            'success': False,
            'error': 'Invalid authentication token'
        }), 401
    
    return user_id, token, None

@app.route('/api/parse', methods=['POST'])
def parse_resume_endpoint():
    """Parse a resume and extract structured information"""
    # Authenticate request
    user_id, token, error_response = authenticate_request()
    if error_response:
        return error_response
    
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
            'questionnaireData': {
                'fullName': parsed_data.get('name', ''),
                'email': parsed_data.get('email', ''),
                'phone': parsed_data.get('phone', ''),
                'experience': ', '.join(parsed_data.get('experience', []))[:100] + '...' if len(', '.join(parsed_data.get('experience', []))) > 100 else ', '.join(parsed_data.get('experience', [])),
                'education': ', '.join(parsed_data.get('education', []))[:100] + '...' if len(', '.join(parsed_data.get('education', []))) > 100 else ', '.join(parsed_data.get('education', [])),
                'skills': parsed_data.get('skills', [])
            }
        }
        
        # Save to database
        resume_id = save_parsed_resume(
            user_id=user_id, 
            token=token,
            file_name=file.filename,
            parsed_data=parsed_data,
            text_content=text_content
        )
        
        # Add the resume ID to the response
        result['resume_id'] = resume_id
        
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
            'error': str(e)
        }), 500

@app.route('/api/extract-text', methods=['POST'])
def extract_text():
    """Extract plain text from a PDF resume"""
    # Authenticate request
    user_id, token, error_response = authenticate_request()
    if error_response:
        return error_response
    
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
        
        # Remove the temporary file
        temp_file_path.unlink(missing_ok=True)
        
        return jsonify({
            'success': True,
            'data': {
                'text': text_content
            }
        })
    
    except Exception as e:
        # Log the full error
        print(f"Error extracting text from PDF: {str(e)}")
        traceback.print_exc()
        
        # Remove the temporary file if it exists
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/resume/<resume_id>', methods=['GET'])
def get_resume_endpoint(resume_id):
    """Retrieve a resume by ID"""
    # Authenticate request
    user_id, token, error_response = authenticate_request()
    if error_response:
        return error_response
    
    try:
        # Get resume from database
        resume = get_resume(resume_id)
        
        if not resume:
            return jsonify({
                'success': False,
                'error': 'Resume not found'
            }), 404
        
        # Check if the resume belongs to the authenticated user
        if resume.get('user_id') != user_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to resume'
            }), 403
        
        return jsonify({
            'success': True,
            'data': resume
        })
    
    except Exception as e:
        # Log the full error
        print(f"Error retrieving resume: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/resumes', methods=['GET'])
def get_user_resumes_endpoint():
    """Retrieve all resumes for a user"""
    # Authenticate request
    user_id, token, error_response = authenticate_request()
    if error_response:
        return error_response
    
    try:
        # Get resumes from database
        resumes = get_user_resumes(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'resumes': resumes,
                'count': len(resumes)
            }
        })
    
    except Exception as e:
        # Log the full error
        print(f"Error retrieving user resumes: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Starting Python resume parser server on port {PORT}...")
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=PORT, debug=DEBUG) 