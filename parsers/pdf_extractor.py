"""
PDF text extraction module.
This module provides functionality to extract text from PDF files using multiple methods
and combines them for the best possible result.
"""
import os
import re
import shutil
from pathlib import Path
import PyPDF2
from pdfminer.high_level import extract_text as pdfminer_extract_text
import tempfile

# Try to import OCR libraries, but don't fail if they're not available
OCR_AVAILABLE = False
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    
    # Check if tesseract is installed
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        OCR_AVAILABLE = True
    else:
        print("Warning: Tesseract OCR binary not found in PATH. OCR functionality disabled.")
except ImportError:
    print("Warning: OCR libraries not installed. OCR functionality disabled.")

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using multiple methods and return the best result.
    
    Args:
        pdf_path (str or Path): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Method 1: PyPDF2
    pypdf2_text = extract_with_pypdf2(pdf_path)
    
    # Method 2: pdfminer.six
    pdfminer_text = extract_with_pdfminer(pdf_path)
    
    # If text methods didn't extract much content, try OCR if available
    texts = [
        (pypdf2_text, len(pypdf2_text), "PyPDF2"),
        (pdfminer_text, len(pdfminer_text), "pdfminer.six")
    ]
    
    if max(len(pypdf2_text), len(pdfminer_text)) < 100 and OCR_AVAILABLE:
        print("Text extraction methods yielded little content. Trying OCR...")
        ocr_text = extract_with_ocr(pdf_path)
        texts.append((ocr_text, len(ocr_text), "OCR"))
    elif max(len(pypdf2_text), len(pdfminer_text)) < 100:
        print("Warning: This appears to be an image-based PDF, but OCR is not available.")
        print("Install Tesseract OCR and required Python packages for better results.")
    
    # Sort by text length in descending order
    texts.sort(key=lambda x: x[1], reverse=True)
    
    # Log the extraction results
    for text, length, method in texts:
        print(f"{method} extracted {length} characters")
    
    # Use the text with the most content
    best_text = texts[0][0]
    
    # Clean up the text
    cleaned_text = clean_text(best_text)
    
    return cleaned_text

def extract_with_pypdf2(pdf_path):
    """Extract text from PDF using PyPDF2"""
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text() + "\n\n"
        return text
    except Exception as e:
        print(f"PyPDF2 extraction failed: {str(e)}")
        return ""

def extract_with_pdfminer(pdf_path):
    """Extract text from PDF using pdfminer.six"""
    try:
        return pdfminer_extract_text(pdf_path)
    except Exception as e:
        print(f"pdfminer.six extraction failed: {str(e)}")
        return ""

def extract_with_ocr(pdf_path):
    """Extract text from PDF using OCR (Optical Character Recognition)"""
    if not OCR_AVAILABLE:
        return ""
        
    try:
        text = ""
        # Create a temporary directory for the images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            images = convert_from_path(pdf_path, output_folder=temp_dir)
            
            # Extract text from each image using OCR
            for i, image in enumerate(images):
                # Use pytesseract to extract text
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n\n"
                
        return text
    except Exception as e:
        print(f"OCR extraction failed: {str(e)}")
        return ""

def clean_text(text):
    """
    Clean and format the extracted text.
    
    Args:
        text (str): The extracted text to clean
        
    Returns:
        str: Cleaned and formatted text
    """
    if not text:
        return ""
    
    # Replace multiple spaces and tabs with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize newlines
    text = re.sub(r'\r\n', '\n', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Fix spacing after punctuation
    text = re.sub(r'([.!?])\s*(\w)', r'\1 \2', text)
    
    # Improve section detection for resumes
    sections = ['education', 'experience', 'skills', 'work history', 'projects', 
                'certifications', 'achievements', 'summary', 'objective']
    
    for section in sections:
        # Create better spacing around section headers (case insensitive)
        pattern = re.compile(r'(\w)(\s*' + section + r'\s*)(\w)', re.IGNORECASE)
        text = pattern.sub(r'\1\n\n\2\n\n\3', text)
    
    # Final trim
    text = text.strip()
    
    return text 