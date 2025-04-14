#!/bin/bash

# Run the Python Resume Parser

# Ensure virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('maxent_ne_chunker', quiet=True); nltk.download('words', quiet=True)"

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
fi

# Run the server
echo "Starting Python Resume Parser server..."
python app.py 