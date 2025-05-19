"""
Main application module for resume parsing.
"""
import os
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
from parsers.pdf_extractor import extract_text_from_pdf
from parsers.resume_parser import parse_resume
from functools import wraps

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

# Configuration
PORT = int(os.getenv("PORT", 5002))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
API_TOKEN = os.getenv("API_TOKEN", "b23ebd32uiedb3uibd3")  # Set your secret token here

# Create temporary upload directory
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "resume-uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

def require_token(f):
    """Decorator to require API token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token.replace('Bearer ', '') != API_TOKEN:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API token'
            }), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/parse', methods=['POST', 'OPTIONS'])
@require_token
def parse_resume_endpoint():
    """Parse resume and extract information"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
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
        
        # Delete temporary file
        temp_file_path.unlink(missing_ok=True)
        
        # Add raw content to parsed data
        parsed_data['raw_content'] = text_content
        
        # Return simplified response format
        return jsonify({
            'success': True,
            'data': {
                'content': parsed_data,
                'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content
            }
        })
        
    except Exception as e:
        # Clean up temp file in case of error
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
            
        return jsonify({
            'success': False,
            'error': f'Error parsing resume: {str(e)}'
        }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Resume parser server is running',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print(f"Starting resume parser server on port {PORT}...")
    print(f"Debug mode: {DEBUG}")
    print(f"Upload directory: {UPLOAD_FOLDER}")
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=PORT, debug=DEBUG)