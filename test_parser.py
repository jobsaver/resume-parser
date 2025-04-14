#!/usr/bin/env python3
"""
Test script for resume parser.
This script tests the resume parsing functionality without needing to run the full API server.
"""
import os
import argparse
import json
from pathlib import Path
from parsers.pdf_extractor import extract_text_from_pdf
from parsers.resume_parser import parse_resume

def main():
    """Main function that parses command line arguments and tests the resume parser"""
    parser = argparse.ArgumentParser(description='Test resume parser functionality')
    parser.add_argument('pdf_path', help='Path to the PDF resume to parse')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    try:
        print(f"Extracting text from {pdf_path}...")
        text_content = extract_text_from_pdf(pdf_path)
        
        if args.verbose:
            print("\n--- Extracted Text ---")
            print(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)
            print("----------------------\n")
        else:
            print(f"Extracted {len(text_content)} characters of text")
        
        print("Parsing resume data...")
        parsed_data = parse_resume(pdf_path, text_content)
        
        print("\n--- Parsed Resume Data ---")
        print(json.dumps(parsed_data, indent=2))
        print("---------------------------")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 