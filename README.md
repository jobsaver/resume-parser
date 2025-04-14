# Resume Parser with OCR Support

A Python-based resume parsing API that extracts structured information from resume PDFs, including both text-based and image-based (scanned) PDFs.

## Features

- Extract text from PDF resumes using multiple extraction methods
- OCR support for scanned or image-based PDFs (requires Tesseract)
- Extract key information including:
  - Name
  - Email
  - Phone
  - Skills
  - Education
  - Experience
  - Summary
- Clean and format extracted text
- REST API with Flask

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`
- Tesseract OCR (optional, for handling image-based PDFs)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. For OCR support (optional but recommended):
   
   - **macOS**:
     ```
     brew install tesseract
     ```
   
   - **Ubuntu/Debian**:
     ```
     sudo apt update
     sudo apt install tesseract-ocr
     ```
   
   - **Windows**:
     Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Usage

1. Start the API server:
   ```
   python app.py
   ```

2. API Endpoints:
   
   - **Parse Resume:**
     ```
     POST /api/parse
     ```
     Form data: `resume` (PDF file)
   
   - **Extract Text Only:**
     ```
     POST /api/extract-text
     ```
     Form data: `resume` (PDF file)
   
   - **Health Check:**
     ```
     GET /health
     ```

## Sample Request (with curl)

```bash
curl -X POST -F "resume=@/path/to/resume.pdf" http://localhost:5002/api/parse
```

## OCR Support

For image-based PDFs (scanned documents), the system will try to use OCR if:

1. The text extraction methods yield minimal content
2. Tesseract is installed and available in the system PATH
3. Required Python packages (pytesseract, pdf2image, Pillow) are installed

If OCR is not available, the system will still work with text-based PDFs, but may not extract much content from image-based ones.

## Troubleshooting

- **OCR not working**: Make sure Tesseract is installed and available in your PATH
- **PDF processing fails**: Check if the PDF is corrupted or password-protected
- **Empty results**: Try with a different PDF to see if the issue is specific to one file

## License

[Specify your license here]# resume-parser
