# ATS Resume Parser API

This API allows you to extract structured information from resumes in PDF format. It provides comprehensive parsing capabilities using hybrid approaches that combine rule-based extraction, NLP techniques, and machine learning.

## Features

- Extract basic information (name, email, phone, LinkedIn)
- Identify skills across multiple industries (500+ pre-defined skills)
- Extract education and work experience
- Detect custom sections and key-value pairs
- Recognize industry-specific terminology

## Setup

### Requirements

```
# Core dependencies
flask==2.3.3
flask-cors==4.0.0
python-dotenv==1.0.0
PyPDF2==3.0.1
pdfminer.six==20221105
nltk>=3.6.2
pymongo==4.6.1
dnspython==2.5.0
numpy>=1.19.0
scipy>=1.6.0
joblib>=1.0.0
pandas>=1.3.0

# Optional OCR capabilities
pytesseract==0.3.10
Pillow>=10.4.0
pdf2image==1.16.3
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Start the server: `python app.py` or `bash run.sh`

## API Endpoints

### Extract Only

Extracts structured information from a resume PDF file without saving to the database.

```
POST /api/extract-only
```

**Parameters**
- `resume` - PDF file (multipart/form-data)

**Example Request**

```bash
curl -X POST \
  -F "resume=@/path/to/resume.pdf" \
  http://localhost:5002/api/extract-only
```

**Example Response**

```json
{
  "success": true,
  "data": {
    "parsedData": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1 555-123-4567",
      "linkedin": "linkedin.com/in/johndoe",
      "location": "San Francisco, CA",
      "websites": ["johndoe.com"],
      "skills": ["Python", "JavaScript", "Machine Learning", "React", "Data Analysis"],
      "education": ["Bachelor of Science in Computer Science, Stanford University, 2015-2019"],
      "experience": ["Software Engineer, Tech Corp, Jan 2019 - Present", "Intern, Tech Startup, Summer 2018"],
      "summary": "Experienced software engineer with a focus on machine learning applications."
    },
    "textContent": "First 1000 characters of extracted text..."
  }
}
```

### Save Resume

Extracts resume data, saves to the database, and replaces existing data if the same user ID exists.

```
POST /api/save-resume
```

**Authentication Required**
- `token` - Authentication token
- `user_id` - User ID

**Parameters**
- `resume` - PDF file (multipart/form-data)
- `resume_id` - Optional resume ID (form data or query parameter)
- `format` - Resume format, defaults to 'standard' (form data or query parameter)
- `resume_url` - Optional URL where the resume is stored (form data)

**Example Request**

```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -F "user_id={user_id}" \
  -F "resume=@/path/to/resume.pdf" \
  -F "resume_id=12345" \
  -F "format=standard" \
  -F "resume_url=https://example.com/resumes/12345.pdf" \
  http://localhost:5002/api/save-resume
```

**Example Response**

```json
{
  "success": true,
  "data": {
    "resume_id": "5f4dcc3b5aa765d61d8327deb882cf99",
    "user_id": "user123",
    "content": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1 555-123-4567",
      "linkedin": "linkedin.com/in/johndoe",
      "location": "San Francisco, CA",
      "websites": ["johndoe.com"],
      "skills": ["Python", "JavaScript", "Machine Learning", "React", "Data Analysis"],
      "education": ["Bachelor of Science in Computer Science, Stanford University, 2015-2019"],
      "experience": ["Software Engineer, Tech Corp, Jan 2019 - Present", "Intern, Tech Startup, Summer 2018"],
      "summary": "Experienced software engineer with a focus on machine learning applications."
    },
    "url": "https://example.com/resumes/12345.pdf",
    "format": "standard"
  }
}
```

## Authentication

The API uses simple token-based authentication. To authenticate requests:

1. Add a `token` parameter in the request header (`Authorization: Bearer <token>`), query parameters, or form data.
2. Add a `user_id` parameter in query parameters or form data.

Tokens are defined in environment variables with the format `TOKEN_<user_id>=<token_value>`.

## Error Handling

All endpoints return standard JSON responses with the following structure:

```json
// Success response
{
  "success": true,
  "data": {
    // Response data
  }
}

// Error response
{
  "success": false,
  "error": "Error message"
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
