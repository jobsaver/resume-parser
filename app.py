"""
Main application module.
"""
import os
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, url_for, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import atexit
import tempfile

# Load environment variables
load_dotenv()

# Import routes
from routes.parser_routes import parser_bp
from routes.builder_routes import builder_bp

# Import database
from database import init_db, close_db

# Import utilities
from utils.url import get_public_download_url

# Create Flask app
app = Flask(__name__, static_folder='static')

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

# Configuration
PORT = int(os.getenv("PORT", 5002))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}")

# Configure maximum file size (10MB)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Create upload directory
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "resume-uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Register blueprints
app.register_blueprint(parser_bp)
app.register_blueprint(builder_bp)

# Initialize database connection
init_db()

# Register function to close database connection on application exit
atexit.register(close_db)

# Public download route
@app.route('/public/download/<path:filename>')
def download_public_file(filename):
    """Serve public download files"""
    try:
        # Get file from temp directory
        temp_dir = Path(tempfile.gettempdir())
        
        # First check resume-uploads directory
        file_path = temp_dir / "resume-uploads" / filename
        if not file_path.exists():
            # Then check rendercv-temp directory
            file_path = temp_dir / "rendercv-temp" / filename
            if not file_path.exists():
                # Search in subdirectories
                for root, _, files in os.walk(temp_dir / "rendercv-temp"):
                    if filename in files:
                        file_path = Path(root) / filename
                        break
        
        if file_path.exists():
            return send_file(
                file_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error serving file: {str(e)}'
        }), 500

# Static file routes
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

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Python resume parser server is running',
        'version': '1.0.0',
        'endpoints': {
            'parser': [
                '/api/extract-only',
                '/api/save-resume',
                '/api/download-resume/<resume_id>'
            ],
            'builder': [
                '/api/themes',
                '/api/create-resume',
                '/api/templates',
                '/api/templates/<template_id>',
                '/api/templates/<template_id>/preview',
                '/api/resume/create'
            ]
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 10MB'
    }), 413

if __name__ == '__main__':
    print(f"Starting Python resume parser server on port {PORT}...")
    print(f"Debug mode: {DEBUG}")
    print(f"Upload directory: {UPLOAD_FOLDER}")
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=PORT, debug=DEBUG)