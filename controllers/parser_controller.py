"""
Controller for resume parsing functionality.
Handles the logic for extracting and saving resume data.
"""
import os
import time
import uuid
from pathlib import Path
import tempfile
from flask import jsonify, current_app, request
from urllib.parse import urljoin
from parsers.pdf_extractor import extract_text_from_pdf
from parsers.resume_parser import parse_resume
from database import get_user_resumes, delete_user_resumes, save_resume_document
from storage import upload_file_to_spaces, generate_spaces_key, delete_file_from_spaces

# Configure upload folder
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "resume-uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

def get_pdf_url(file_path, resume_id):
    """Helper function to generate PDF URL"""
    if os.path.isabs(file_path):
        # For local files, generate a URL using the download endpoint
        base_url = request.host_url.rstrip('/')
        return f"{base_url}/api/download-resume/{resume_id}"
    return file_path  # Return as is if it's already a URL

def extract_resume(file):
    """
    Extract data from resume without saving
    
    Args:
        file: The uploaded file object
        
    Returns:
        tuple: (success, result)
    """
    try:
        # Save the file temporarily
        temp_file_path = UPLOAD_FOLDER / file.filename
        file.save(temp_file_path)
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(temp_file_path)
        
        # Parse the resume
        parsed_data = parse_resume(temp_file_path, text_content)
        
        # Create a resume_id
        temp_resume_id = f"temp_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Generate PDF URL
        pdf_url = get_pdf_url(str(temp_file_path), temp_resume_id)
        
        # Create the response
        result = {
            'resume_id': temp_resume_id,
            'user_id': 'anonymous',
            'content': parsed_data,
            'format': 'standard',
            'file_url': pdf_url,
            'pdf_url': pdf_url,  # Add consistent pdf_url field
            'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content,
            'success': True
        }
        
        return True, result
        
    except Exception as e:
        # Clean up temp file in case of error
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        return False, str(e)

def save_resume(file, user_id, resume_format='standard'):
    """
    Save resume data and file
    
    Args:
        file: The uploaded file object
        user_id: User ID
        resume_format: Resume format (optional)
        
    Returns:
        tuple: (success, result)
    """
    try:
        # Save the file temporarily
        temp_file_path = UPLOAD_FOLDER / file.filename
        file.save(temp_file_path)
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(temp_file_path)
        
        # Parse the resume
        parsed_data = parse_resume(temp_file_path, text_content)
        
        # Create a resume_id
        resume_id = str(uuid.uuid4())
        
        # Delete existing resumes for this user if any
        existing_resumes = get_user_resumes(user_id)
        if existing_resumes:
            # Delete from storage
            for resume in existing_resumes:
                url = resume.get('url')
                if url:
                    url_parts = url.split('/')
                    if len(url_parts) >= 4:
                        object_key = '/'.join(url_parts[3:])
                        delete_file_from_spaces(object_key)
            
            # Delete from database
            delete_user_resumes(user_id)
        
        # Upload file to storage
        spaces_key = generate_spaces_key(user_id, resume_id, file.filename)
        upload_success, spaces_result = upload_file_to_spaces(temp_file_path, spaces_key, 'application/pdf')
        
        if not upload_success:
            raise Exception(f'Error uploading file to storage: {spaces_result}')
        
        # Store the file URL
        file_url = spaces_result if upload_success else get_pdf_url(str(temp_file_path), resume_id)
        
        # Create document
        document = {
            "resume_id": resume_id,
            "user_id": user_id,
            "content": parsed_data,
            "url": file_url,
            "format": resume_format
        }
        
        # Save to database
        saved_id = save_resume_document(document)
        
        # Create response
        result = {
            'resume_id': saved_id,
            'user_id': user_id,
            'content': parsed_data,
            'format': resume_format,
            'file_url': file_url,
            'pdf_url': file_url,  # Add consistent pdf_url field
            'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content,
            'success': True
        }
        
        return True, result
        
    except Exception as e:
        # Clean up temp file in case of error
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        return False, str(e)

def download_resume(user_id, resume_id):
    """
    Get download URL or path for a resume
    
    Args:
        user_id: User ID
        resume_id: Resume ID
        
    Returns:
        tuple: (success, result)
    """
    try:
        # Get user's resumes
        resumes = get_user_resumes(user_id)
        
        # Find the resume
        resume = None
        for r in resumes:
            if r.get('resume_id') == resume_id:
                resume = r
                break
        
        if not resume:
            return False, f'Resume with ID {resume_id} not found'
        
        # Get the file URL 
        file_url = resume.get('url')
        if not file_url:
            return False, f'No file URL found for resume with ID {resume_id}'
            
        # Generate PDF URL if needed
        pdf_url = get_pdf_url(file_url, resume_id)
        
        return True, {
            'success': True,
            'file_url': pdf_url,
            'pdf_url': pdf_url,  # Add consistent pdf_url field
            'resume_id': resume_id
        }
        
    except Exception as e:
        return False, str(e)