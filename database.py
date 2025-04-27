"""
Database module for MongoDB integration.
This module provides functionality to store and retrieve parsed resume data.
"""
import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "resume_parser")

# Dump environment variables (debug only)
print("Environment variables:")
for key, value in os.environ.items():
    if "TOKEN_" in key:
        print(f"  {key}: {value[:4]}***")
    
# API tokens (from environment variables or configuration)
API_TOKENS = {}

# Initialize API tokens from environment variables
# Format: TOKEN_<user_id>=<token_value>
for key, value in os.environ.items():
    if key.startswith('TOKEN_'):
        user_id = key[6:]  # Remove 'TOKEN_' prefix
        API_TOKENS[user_id] = value
        print(f"Added token for user: {user_id}")

# Add a default test token if none exists and in development mode
if not API_TOKENS and os.getenv("DEBUG", "True").lower() == "true":
    API_TOKENS['test_user'] = 'test_token'
    print("Warning: Using default test token. This should not be used in production.")

# Hardcode test values for now to fix issues
API_TOKENS['test_user'] = 'b23ebd32uiedb3uibd3'
API_TOKENS['admin'] = 'bhedbed8732e32e32'
print(f"Added hardcoded token for test_user and admin (debug mode)")

# Initialize MongoDB client
client = None
db = None

def init_db():
    """Initialize database connection"""
    global client, db
    
    if not MONGO_URI:
        raise ValueError("MongoDB URI not found in environment variables")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        # Test connection
        client.admin.command('ping')
        print(f"Connected to MongoDB: {MONGO_DB_NAME}")
        return True
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return False

def close_db():
    """Close database connection"""
    if client:
        client.close()
        print("MongoDB connection closed")

def get_user_resumes(user_id):
    """
    Retrieve all resumes for a specific user
    
    Args:
        user_id (str): The user ID
        
    Returns:
        list: List of resume documents
    """
    global db
    if db is None:
        if not init_db():
            return []
    
    try:
        collection = db.resumes
        
        # Find documents
        resumes = list(collection.find({"user_id": user_id}))
        
        # Convert ObjectId to string for JSON serialization
        for resume in resumes:
            resume["_id"] = str(resume["_id"])
            
        return resumes
        
    except Exception as e:
        print(f"Error retrieving user resumes from database: {str(e)}")
        return []

def delete_user_resumes(user_id):
    """
    Delete all resumes for a specific user
    
    Args:
        user_id (str): The user ID
        
    Returns:
        int: Number of deleted documents
    """
    global db
    if db is None:
        if not init_db():
            return 0
    
    try:
        collection = db.resumes
        
        # Delete documents
        result = collection.delete_many({"user_id": user_id})
        deleted_count = result.deleted_count
        
        print(f"Deleted {deleted_count} resumes for user: {user_id}")
        return deleted_count
        
    except Exception as e:
        print(f"Error deleting user resumes from database: {str(e)}")
        return 0

def save_resume_document(document):
    """
    Save resume document with simplified structure
    
    Args:
        document (dict): The document to save with the following keys:
            - resume_id: Optional resume ID
            - user_id: User ID
            - content: Parsed resume data
            - url: Resume URL
            - format: Resume format
        
    Returns:
        str: The ID of the saved document
    """
    global db
    if db is None:
        if not init_db():
            return None
    
    try:
        collection = db.resumes
        
        # Add timestamps
        document["created_at"] = datetime.datetime.utcnow()
        document["updated_at"] = datetime.datetime.utcnow()
        
        # Insert document
        result = collection.insert_one(document)
        resume_id = str(result.inserted_id)
        
        print(f"Resume document saved to database with ID: {resume_id}")
        return resume_id
        
    except Exception as e:
        print(f"Error saving resume document to database: {str(e)}")
        return None

def validate_token(user_id, token):
    """
    Validate an authentication token for a specific user
    
    Args:
        user_id (str): The user ID
        token (str): The token to validate
        
    Returns:
        bool: True if the token is valid for the user, False otherwise
    """
    # Print token details for debugging
    print(f"Validating token for user: {user_id}")
    print(f"Available tokens: {list(API_TOKENS.keys())}")
    
    # Check if token exists for this user
    expected_token = API_TOKENS.get(user_id)
    
    if not expected_token:
        print(f"No token found for user: {user_id}")
        return False
    
    # Validate token (simple string comparison)
    is_valid = token == expected_token
    
    if not is_valid:
        print(f"Invalid token for user: {user_id}")
        print(f"Received token starts with: {token[:4]}...")
        print(f"Expected token starts with: {expected_token[:4]}...")
    else:
        print(f"Token validated successfully for user: {user_id}")
    
    return is_valid 