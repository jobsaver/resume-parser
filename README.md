# Resume Parser with OCR Support and MongoDB Integration

A Python-based resume parsing API that extracts structured information from resume PDFs, including both text-based and image-based (scanned) PDFs. It stores parsed data in MongoDB and provides authentication.

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
- MongoDB integration for data persistence
- Authentication with user ID and token

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`
- Tesseract OCR (optional, for handling image-based PDFs)
- MongoDB database

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

4. Configure MongoDB:
   - Create a `.env` file with your MongoDB connection string:
     ```
     MONGO_URI=mongodb+srv://username:password@host/
     MONGO_DB_NAME=resume_parser
     ```

## Usage

1. Start the API server:
   ```
   python app.py
   ```
   or use the provided script:
   ```
   ./run.sh
   ```

2. API Endpoints:
   
   - **Parse Resume:**
     ```
     POST /api/parse?user_id=<user_id>&token=<token>
     ```
     Form data: `resume` (PDF file)
   
   - **Extract Text Only:**
     ```
     POST /api/extract-text?user_id=<user_id>&token=<token>
     ```
     Form data: `resume` (PDF file)
   
   - **Get Resume by ID:**
     ```
     GET /api/resume/<resume_id>?user_id=<user_id>&token=<token>
     ```
   
   - **Get All User Resumes:**
     ```
     GET /api/user/resumes?user_id=<user_id>&token=<token>
     ```
   
   - **Health Check:**
     ```
     GET /health
     ```

## Authentication

All API endpoints (except health check) require authentication:

- **user_id**: The ID of the user making the request
- **token**: Authentication token

You can provide these parameters in two ways:

1. Query parameters: `?user_id=12345&token=your-token`
2. Headers: Include `Authorization: Bearer your-token` header and `user_id` as a query parameter

## Sample Requests (with curl)

### Parse Resume
```bash
curl -X POST -F "resume=@/path/to/resume.pdf" "http://localhost:5002/api/parse?user_id=12345&token=your-token"
```

### Get User Resumes
```bash
curl -X GET "http://localhost:5002/api/user/resumes?user_id=12345&token=your-token"
```

## OCR Support

For image-based PDFs (scanned documents), the system will try to use OCR if:

1. The text extraction methods yield minimal content
2. Tesseract is installed and available in the system PATH
3. Required Python packages (pytesseract, pdf2image, Pillow) are installed

If OCR is not available, the system will still work with text-based PDFs, but may not extract much content from image-based ones.

## MongoDB Data Structure

Resumes are stored in the following format:

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "file_name": "string",
  "parsed_data": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "skills": ["string"],
    "experience": ["string"],
    "education": ["string"],
    "summary": "string"
  },
  "text_content": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Troubleshooting

- **OCR not working**: Make sure Tesseract is installed and available in your PATH
- **PDF processing fails**: Check if the PDF is corrupted or password-protected
- **Empty results**: Try with a different PDF to see if the issue is specific to one file
- **MongoDB connection issues**: Verify your connection string and network settings

## License

[Specify your license here]
