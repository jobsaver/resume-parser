import os
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Import parsers
from parsers.pdf_extractor import extract_text_from_pdf
from parsers.resume_parser import parse_resume

app = Flask(__name__)
CORS(app)

# Configuration
PORT = int(os.getenv("PORT", 5002))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "resume-uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Configure maximum file size (10MB)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Python resume parser server is running',
        'version': '1.0.0'
    })

@app.route('/api/parse', methods=['POST'])
def parse_resume_endpoint():
    """Parse a resume and extract structured information"""
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

if __name__ == '__main__':
    print(f"Starting Python resume parser server on port {PORT}...")
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=PORT, debug=DEBUG) 