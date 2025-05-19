# Resume Parser API

Simple API to extract structured information from resumes in PDF format. It uses regex patterns and NLP techniques to extract data from resume content.

## Features

- Extract basic information (name, email, phone)
- Identify skills using natural language processing
- Extract education and work experience sections
- Extract certification information
- Raw text content included in response
- Token-based API authentication
- PDF text extraction with OCR support

## Setup

### Requirements

```
flask>=2.0.1
flask-cors==4.0.0
PyPDF2==3.0.1
pdfminer.six==20221105
nltk>=3.6.2
pytesseract==0.3.10
pillow>=10.4.0
pdf2image==1.16.3
spacy>=3.0.0
scikit-learn>=1.0.0
gensim>=4.0.0
python-dotenv==1.0.1
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variable for API_TOKEN
4. Start the server: `python app.py` or `bash run.sh`

## API Endpoint

### Parse Resume

Extracts structured information from a resume PDF file.

```
POST /api/parse
```

**Authentication Required**
- Header: `Authorization: Bearer your-secret-token-here`

**Parameters**
- `resume` - PDF file (multipart/form-data)

**Example Request**

```bash
curl -X POST \
  -H "Authorization: Bearer your-secret-token-here" \
  -F "resume=@/path/to/resume.pdf" \
  http://localhost:5002/api/parse
```

**Example Response**

```json
{
  "success": true,
  "data": {
    "content": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1 555-123-4567",
      "skills": ["Python", "JavaScript", "Machine Learning", "React", "Data Analysis"],
      "education": ["Bachelor of Science in Computer Science, Stanford University, 2015-2019"],
      "experience": ["Software Engineer, Tech Corp, Jan 2019 - Present", "Intern, Tech Startup, Summer 2018"],
      "certifications": ["AWS Certified Developer", "Google Cloud Professional"],
      "raw_content": "First portion of extracted text..."
    },
    "textContent": "First 1000 characters of extracted text..."
  }
}
```

### Health Check

Check if the API is running.

```
GET /health
```

**Example Response**

```json
{
  "status": "ok",
  "message": "Resume parser server is running",
  "version": "1.0.0"
}
```

## Error Handling

All endpoints return standard JSON responses:

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

## Authentication

The API uses token-based authentication:

1. Set your API token in the environment variable `API_TOKEN`
2. Include the token in the Authorization header: `Authorization: Bearer your-secret-token-here`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
