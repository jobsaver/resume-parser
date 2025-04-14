# ATS Resume Parser API

This API allows you to extract structured information from resumes in PDF format. It provides comprehensive parsing capabilities using hybrid approaches that combine rule-based extraction, NLP techniques, and machine learning.

## Features

- Extract basic information (name, email, phone, LinkedIn)
- Identify skills across multiple industries (500+ pre-defined skills)
- Extract education and work experience
- Detect custom sections and key-value pairs
- Recognize industry-specific terminology
- Machine learning based content clustering (when available)
- Named entity recognition with spaCy (when available)
- Topic modeling with Gensim (when available)

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

# Enhanced features (optional but recommended)
scikit-learn>=1.0.0
numpy>=1.19.0
scipy>=1.6.0
pandas>=1.3.0
spacy>=3.0.0
gensim>=4.0.0
python-Levenshtein>=0.12.0

# Optional OCR capabilities
pytesseract==0.3.10
Pillow==10.0.0
pdf2image==1.16.3
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install spaCy model: `python -m spacy download en_core_web_sm`
4. Set up environment variables (see `.env.example`)
5. Start the server: `python app.py`

## API Endpoints

### Parse Resume

Extracts structured information from a resume PDF file.

```
POST /api/parse
```

**Authentication Required**
- `token` - Authentication token
- `user_id` - User ID

**Parameters**
- `resume` - PDF file (multipart/form-data)

**Example Request**

```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -F "user_id={user_id}" \
  -F "resume=@/path/to/resume.pdf" \
  http://localhost:5002/api/parse
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
      "summary": "Experienced software engineer with a focus on machine learning applications.",
      "industry": ["Technology", "Software"],
      "job_titles": ["Software Engineer", "Machine Learning Engineer"],
      "years_of_experience": 5,
      "projects": ["Portfolio Website", "ML Classification Tool"],
      "certifications": ["AWS Certified Developer", "Google Cloud Professional"],
      "languages": ["English (native)", "Spanish (intermediate)"],
      "dynamic_fields": {
        "custom_sections": {
          "technical expertise": ["Machine Learning", "Full Stack Development", "DevOps"]
        },
        "key_value_pairs": {
          "availability": "Immediate",
          "salary expectation": "$120,000",
          "willing to relocate": "Yes"
        },
        "domain_terminology": ["neural networks", "data visualization", "cloud infrastructure"],
        "entities": {
          "organizations": ["Tech Corp", "Stanford University", "Google"],
          "locations": ["San Francisco", "New York", "Remote"]
        },
        "topics": [
          {
            "id": 0,
            "terms": ["software", "development", "engineering", "systems", "design"]
          }
        ]
      }
    },
    "textContent": "First 1000 characters of extracted text...",
    "questionnaireData": {
      "fullName": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1 555-123-4567",
      "linkedIn": "linkedin.com/in/johndoe",
      "location": "San Francisco, CA",
      "websites": ["johndoe.com"],
      "summary": "Experienced software engineer with a focus on machine learning applications.",
      "experience": "Software Engineer, Tech Corp, Jan 2019 - Present...",
      "education": "Bachelor of Science in Computer Science, Stanford University...",
      "skills": ["Python", "JavaScript", "Machine Learning", "React", "Data Analysis"],
      "industry": ["Technology", "Software"],
      "jobTitles": ["Software Engineer", "Machine Learning Engineer"],
      "yearsOfExperience": 5,
      "domainTerminology": ["neural networks", "data visualization", "cloud infrastructure"],
      "organizations": ["Tech Corp", "Stanford University", "Google"]
    },
    "resume_id": "5f4dcc3b5aa765d61d8327deb882cf99"
  }
}
```

### Extract Text Only

Extracts plain text from a resume PDF without parsing for structured data.

```
POST /api/extract-text
```

**Authentication Required**
- `token` - Authentication token
- `user_id` - User ID

**Parameters**
- `resume` - PDF file (multipart/form-data)

**Example Request**

```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -F "user_id={user_id}" \
  -F "resume=@/path/to/resume.pdf" \
  http://localhost:5002/api/extract-text
```

**Example Response**

```json
{
  "success": true,
  "data": {
    "text": "Full text content of the resume..."
  }
}
```

### Get Resume by ID

Retrieves a previously parsed resume by its ID.

```
GET /api/resume/:resume_id
```

**Authentication Required**
- `token` - Authentication token
- `user_id` - User ID (must match the original uploader)

**Example Request**

```bash
curl -X GET \
  -H "Authorization: Bearer {token}" \
  "http://localhost:5002/api/resume/5f4dcc3b5aa765d61d8327deb882cf99?user_id={user_id}"
```

**Example Response**

```json
{
  "success": true,
  "data": {
    "_id": "5f4dcc3b5aa765d61d8327deb882cf99",
    "user_id": "user123",
    "file_name": "john_doe_resume.pdf",
    "parsed_data": { /* Same structure as in /api/parse response */ },
    "text_content": "Full text content of the resume...",
    "created_at": "2023-06-01T12:00:00.000Z",
    "updated_at": "2023-06-01T12:00:00.000Z"
  }
}
```

### Get All User Resumes

Retrieves all resumes uploaded by a specific user.

```
GET /api/user/resumes
```

**Authentication Required**
- `token` - Authentication token
- `user_id` - User ID

**Example Request**

```bash
curl -X GET \
  -H "Authorization: Bearer {token}" \
  "http://localhost:5002/api/user/resumes?user_id={user_id}"
```

**Example Response**

```json
{
  "success": true,
  "data": {
    "resumes": [
      {
        "_id": "5f4dcc3b5aa765d61d8327deb882cf99",
        "user_id": "user123",
        "file_name": "john_doe_resume.pdf",
        "parsed_data": { /* Same structure as in /api/parse response */ },
        "text_content": "Full text content of the resume...",
        "created_at": "2023-06-01T12:00:00.000Z",
        "updated_at": "2023-06-01T12:00:00.000Z"
      },
      {
        /* Additional resume records */
      }
    ],
    "count": 2
  }
}
```

## Authentication

Authentication is required for all API endpoints. The API supports the following authentication methods:

1. Bearer token in the Authorization header: `Authorization: Bearer {token}`
2. Token in query parameters: `?token={token}&user_id={user_id}`
3. Token in form data: `token={token}&user_id={user_id}`

Authentication tokens are managed via environment variables:
- Format: `TOKEN_{user_id}={token_value}`
- Example: `TOKEN_test_user=abcdef123456`

## Error Handling

All API endpoints return a JSON response with a `success` field indicating whether the request was successful. In case of an error, the response includes an `error` field with a description of the error.

Example error response:

```json
{
  "success": false,
  "error": "Authentication token is required"
}
```

Common HTTP status codes:
- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid (e.g., missing parameters)
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: The authenticated user is not allowed to access the requested resource
- `404 Not Found`: The requested resource was not found
- `500 Internal Server Error`: An unexpected error occurred on the server

## Advanced Parsing Features

### Dynamic Field Detection

The parser automatically detects fields and sections that are not explicitly defined in the code:

- **Custom Sections**: Identifies uniquely named sections in resumes
- **Key-Value Pairs**: Extracts attributes formatted as key-value pairs
- **Domain Terminology**: Identifies domain-specific terminology using NLP

### Machine Learning Features

When the required dependencies are installed, the parser provides additional ML-powered features:

- **Content Clustering**: Groups similar content using K-means clustering
- **Named Entity Recognition**: Identifies entities like organizations, people, and locations
- **Topic Modeling**: Discovers key themes using Latent Dirichlet Allocation (LDA)

### OCR Capabilities

For image-based PDFs, the parser can use OCR to extract text when the following dependencies are installed:
- pytesseract
- Pillow
- pdf2image

Note: Tesseract OCR must be installed on the system for OCR functionality.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
