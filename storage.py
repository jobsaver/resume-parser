"""
Storage module for handling file uploads to DigitalOcean Spaces.
"""
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pathlib import Path
import mimetypes

# Load environment variables
load_dotenv()

# DigitalOcean Spaces Configuration
SPACES_ENDPOINT = os.getenv('SPACES_ENDPOINT', 'https://blr1.digitaloceanspaces.com')
SPACES_KEY = os.getenv('SPACES_KEY', 'DO00FYCKNN7984HM3NAH')
SPACES_SECRET = os.getenv('SPACES_SECRET', 'W4aDgpNzllP9yHBINioyXuiDYHO05WNnSqXgQmIX5YY')
SPACES_BUCKET = os.getenv('SPACES_BUCKET', 'storage-jobmato')
SPACES_REGION = os.getenv('SPACES_REGION', 'blr1')
SPACES_URL = os.getenv('SPACES_URL', 'https://storage-jobmato.blr1.digitaloceanspaces.com')

# Initialize the S3 client (DigitalOcean Spaces is S3-compatible)
s3_client = boto3.client(
    's3',
    region_name=SPACES_REGION,
    endpoint_url=SPACES_ENDPOINT,
    aws_access_key_id=SPACES_KEY,
    aws_secret_access_key=SPACES_SECRET
)

def upload_file_to_spaces(local_file_path, object_key, content_type=None):
    """
    Upload a file to DigitalOcean Spaces.
    
    Args:
        local_file_path (str or Path): Path to the local file
        object_key (str): The key (path) where the file will be stored in Spaces
        content_type (str, optional): Content type of the file
        
    Returns:
        tuple: (success, url or error message)
    """
    local_file_path = Path(local_file_path)
    
    if not local_file_path.exists():
        return False, f"File not found: {local_file_path}"
    
    # If content_type is not provided, try to guess it
    if content_type is None:
        content_type, _ = mimetypes.guess_type(str(local_file_path))
        if content_type is None:
            content_type = 'application/octet-stream'  # Default content type
    
    try:
        # Upload file to DigitalOcean Spaces
        s3_client.upload_file(
            str(local_file_path),
            SPACES_BUCKET,
            object_key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'  # Make file publicly accessible
            }
        )
        
        # Construct the URL for the uploaded file
        file_url = f"{SPACES_URL}/{object_key}"
        return True, file_url
    
    except ClientError as e:
        print(f"Error uploading file to DigitalOcean Spaces: {str(e)}")
        return False, str(e)
    except Exception as e:
        print(f"Unexpected error uploading file: {str(e)}")
        return False, str(e)

def generate_spaces_key(user_id, resume_id, filename):
    """
    Generate a unique key for storing a file in DigitalOcean Spaces.
    
    Args:
        user_id (str): User ID
        resume_id (str): Resume ID
        filename (str): Original filename
        
    Returns:
        str: Unique key for the file
    """
    # Extract file extension
    _, ext = os.path.splitext(filename)
    
    # Create a path structure: resumes/user_id/resume_id.ext
    return f"resumes/{user_id}/{resume_id}{ext}"

def get_file_from_spaces(object_key):
    """
    Get a file from DigitalOcean Spaces.
    
    Args:
        object_key (str): The key (path) of the file in Spaces
        
    Returns:
        tuple: (success, content or error message)
    """
    try:
        # Get file from DigitalOcean Spaces
        response = s3_client.get_object(
            Bucket=SPACES_BUCKET,
            Key=object_key
        )
        
        # Read the content of the file
        content = response['Body'].read()
        return True, content
    
    except ClientError as e:
        print(f"Error getting file from DigitalOcean Spaces: {str(e)}")
        return False, str(e)
    except Exception as e:
        print(f"Unexpected error getting file: {str(e)}")
        return False, str(e)

def delete_file_from_spaces(object_key):
    """
    Delete a file from DigitalOcean Spaces.
    
    Args:
        object_key (str): The key (path) of the file in Spaces
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Delete file from DigitalOcean Spaces
        s3_client.delete_object(
            Bucket=SPACES_BUCKET,
            Key=object_key
        )
        
        return True, f"File {object_key} deleted successfully"
    
    except ClientError as e:
        print(f"Error deleting file from DigitalOcean Spaces: {str(e)}")
        return False, str(e)
    except Exception as e:
        print(f"Unexpected error deleting file: {str(e)}")
        return False, str(e) 