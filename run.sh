#!/bin/bash

# Run the Python Resume Parser

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Ensure virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please ensure 'python3-venv' is installed."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi

# Install dependencies with verbose output
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify critical dependencies
echo "Verifying critical dependencies..."
python -c "
try:
    import flask
    import pymongo
    import PyPDF2
    import nltk
    import dotenv
    print('All critical packages verified.')
except ImportError as e:
    print(f'Error: {e}')
    print('Please run: pip install -r requirements.txt')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "Critical dependency check failed. Exiting."
    exit 1
fi

# Download NLTK data
echo "Downloading NLTK data..."
python -c "
try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
    print('NLTK data downloaded successfully.')
except Exception as e:
    print(f'Error downloading NLTK data: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "NLTK data download failed. Exiting."
    exit 1
fi

# Check for Tesseract OCR
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract OCR not found. OCR functionality will be limited."
    echo "To install Tesseract OCR:"
    echo "  - macOS: brew install tesseract"
    echo "  - Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    
    # Make sure MongoDB URI is set
    if grep -q "MONGO_URI=" .env; then
        echo "MongoDB URI is set in .env file."
    else
        echo "WARNING: MongoDB URI is not set in .env file. Please add it manually."
    fi
fi

# Test MongoDB connection
echo "Testing MongoDB connection..."
python -c "
try:
    from database import init_db, close_db
    success = init_db()
    print('Connection successful' if success else 'Connection failed')
    close_db()
except Exception as e:
    print(f'Error testing MongoDB connection: {e}')
    print('Continue anyway? MongoDB storage functionality may be limited.')
"

# Run the server
echo "Starting Python Resume Parser server..."
python app.py 