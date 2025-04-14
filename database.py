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

def save_parsed_resume(user_id, token, file_name, parsed_data, text_content):
    """
    Save parsed resume data to MongoDB
    
    Args:
        user_id (str): The user ID who uploaded the resume
        token (str): Authentication token
        file_name (str): Original file name
        parsed_data (dict): The structured data extracted from the resume
        text_content (str): The raw text content of the resume
        
    Returns:
        str: The ID of the saved document
    """
    if not db:
        if not init_db():
            return None
    
    try:
        collection = db.resumes
        
        # Create document
        document = {
            "user_id": user_id,
            "file_name": file_name,
            "parsed_data": parsed_data,
            "text_content": text_content,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        
        # Insert document
        result = collection.insert_one(document)
        resume_id = str(result.inserted_id)
        
        print(f"Resume saved to database with ID: {resume_id}")
        return resume_id
        
    except Exception as e:
        print(f"Error saving resume to database: {str(e)}")
        return None

def get_resume(resume_id):
    """
    Retrieve a resume from the database by ID
    
    Args:
        resume_id (str): The ID of the resume to retrieve
        
    Returns:
        dict: The resume document, or None if not found
    """
    if not db:
        if not init_db():
            return None
    
    try:
        collection = db.resumes
        
        # Find document
        resume = collection.find_one({"_id": ObjectId(resume_id)})
        
        if resume:
            # Convert ObjectId to string for JSON serialization
            resume["_id"] = str(resume["_id"])
            return resume
        
        return None
        
    except Exception as e:
        print(f"Error retrieving resume from database: {str(e)}")
        return None

def get_user_resumes(user_id):
    """
    Retrieve all resumes for a specific user
    
    Args:
        user_id (str): The user ID
        
    Returns:
        list: List of resume documents
    """
    if not db:
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

def validate_token(token):
    """
    Validate an authentication token
    
    Args:
        token (str): The token to validate
        
    Returns:
        bool: True if the token is valid, False otherwise
    """
    # This is a placeholder for actual token validation logic
    # In a real implementation, you would verify the token against your auth system
    return token is not None and len(token) > 0 