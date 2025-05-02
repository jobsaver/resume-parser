"""
Controller for resume parsing functionality.
Handles the logic for extracting and saving resume data.
"""
import os
import time
import uuid
from pathlib import Path
import tempfile
from flask import jsonify
from parsers.pdf_extractor import extract_text_from_pdf
from parsers.resume_parser import parse_resume
from database import get_user_resumes, delete_user_resumes, save_resume_document
from storage import upload_file_to_spaces, generate_spaces_key, delete_file_from_spaces

# Configure upload folder
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "resume-uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

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
        
        # Create the response
        result = {
            'resume_id': temp_resume_id,
            'user_id': 'anonymous',
            'content': parsed_data,
            'format': 'standard',
            'file_url': '',
            'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content
        }
        
        # Remove the temporary file
        temp_file_path.unlink(missing_ok=True)
        
        return True, result
        
    except Exception as e:
        # Remove the temporary file if it exists
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        return False, str(e)

def save_resume(file, user_id, resume_format='standard'):
    """
    Save resume data to database and storage
    
    Args:
        file: The uploaded file object
        user_id: User ID
        resume_format: Format of the resume
        
    Returns:
        tuple: (success, result)
    """
    try:
        # Generate resume ID
        resume_id = f"{user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Save the file temporarily
        temp_file_path = UPLOAD_FOLDER / file.filename
        file.save(temp_file_path)
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(temp_file_path)
        
        # Parse the resume
        parsed_data = parse_resume(temp_file_path, text_content)
        
        # Get user's existing resumes
        existing_resumes = get_user_resumes(user_id)
        
        # Delete existing resumes if any
        if existing_resumes:
            # Delete from storage
            for resume in existing_resumes:
                if resume.get('url'):
                    url_parts = resume['url'].split('/')
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
        file_url = spaces_result
        
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
            'content': {
                'name': parsed_data.get('name', ''),
                'email': parsed_data.get('email', ''),
                'phone': parsed_data.get('phone', ''),
                'skills': parsed_data.get('skills', []),
                'education': parsed_data.get('education', []),
                'experience': parsed_data.get('experience', []),
                'certifications': parsed_data.get('certifications', []),
                'raw_content': parsed_data.get('raw_content', '')
            },
            'format': resume_format,
            'file_url': file_url,
            'textContent': text_content[:1000] + '...' if len(text_content) > 1000 else text_content
        }
        
        # Remove the temporary file
        temp_file_path.unlink(missing_ok=True)
        
        return True, result
        
    except Exception as e:
        # Remove the temporary file if it exists
        if 'temp_file_path' in locals():
            temp_file_path.unlink(missing_ok=True)
        return False, str(e)

def download_resume(user_id, resume_id):
    """
    Get download URL for a resume
    
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
        
        return True, {'file_url': file_url}
        
    except Exception as e:
        return False, str(e) 