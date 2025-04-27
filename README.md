# ATS Resume Parser API

This API allows you to extract structured information from resumes in PDF format. It provides parsing capabilities using regex patterns and NLP techniques to extract data directly from the resume content.

## Features

- Extract basic information (name, email, phone)
- Identify skills using natural language processing
- Extract education and work experience sections
- Extract certification information
- Store resume PDFs in DigitalOcean Spaces
- Raw text content included in response
- Consistent API response format across endpoints

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
boto3>=1.28.0

# Optional NLP enhancements
spacy>=3.0.0
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Start the server: `python app.py` or `bash run.sh`

## API Endpoints

### Extract Only

Extracts structured information from a resume PDF file without saving to the database. No authentication required.

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
    "resume_id": "temp_1632506789_a7b8c9d0",
    "user_id": "anonymous",
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
    "format": "standard",
    "file_url": "",
    "textContent": "First 1000 characters of extracted text..."
  }
}
```

### Save Resume

Extracts resume data, saves to the database, and stores the PDF in DigitalOcean Spaces. Authentication required.

```
POST /api/save-resume
```

**Authentication Required**
- `token` - Authentication token
- `user_id` - User ID

**Parameters**
- `resume` - PDF file (multipart/form-data)
- `format` - Optional resume format, defaults to 'standard' (form data)

**Notes**
- Resume ID is automatically generated using a combination of user ID, timestamp, and a unique identifier
- PDF file is uploaded to DigitalOcean Spaces for storage and retrieval
- The file URL is stored in the database along with the parsed resume data

**Example Request**

```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -F "user_id={user_id}" \
  -F "resume=@/path/to/resume.pdf" \
  http://localhost:5002/api/save-resume
```

**Example Response**

```json
{
  "success": true,
  "data": {
    "resume_id": "user123_1632506789_a7b8c9d0",
    "user_id": "user123",
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
    "format": "standard",
    "file_url": "https://storage-jobmato.blr1.digitaloceanspaces.com/resumes/user123/user123_1632506789_a7b8c9d0.pdf",
    "textContent": "First 1000 characters of extracted text..."
  }
}
```

## Response Format

Both API endpoints return responses in the same format for consistency:

| Field | Description |
|-------|-------------|
| `resume_id` | Unique identifier for the resume (auto-generated) |
| `user_id` | User ID (`anonymous` for extract-only endpoint) |
| `content` | Parsed resume data including name, email, phone, skills, education, experience, certifications, and raw content |
| `format` | Resume format (always `standard` for extract-only endpoint) |
| `file_url` | URL to the stored PDF file (empty for extract-only endpoint) |
| `textContent` | First 1000 characters of extracted text for preview |

## Authentication

The API uses simple token-based authentication. To authenticate requests:

1. Add a `token` parameter in the request header (`Authorization: Bearer <token>`), query parameters, or form data.
2. Add a `user_id` parameter in query parameters or form data.

Tokens are defined in environment variables with the format `TOKEN_<user_id>=<token_value>`.

## File Storage

Resume files are stored in DigitalOcean Spaces:

1. Files are organized by user ID: `resumes/{user_id}/{resume_id}.pdf`
2. Each file is publicly accessible via the URL returned in the API response
3. Configuration is done through environment variables (see `.env.example`)

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
