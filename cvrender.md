# Resume Maker Documentation

## Resume Structure

The resume maker supports dynamic fields and multiple templates. Here's the complete structure of a resume:

```json
{
  "personal_info": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "website": "string (optional)",
    "linkedin": "string (optional)",
    "github": "string (optional)",
    "summary": "string (optional)"
  },
  "education": [
    {
      "school": "string",
      "degree": "string",
      "field_of_study": "string",
      "start_date": "string (YYYY-MM)",
      "end_date": "string (YYYY-MM or 'Present')",
      "gpa": "string (optional)",
      "courses": ["string"],
      "achievements": ["string (optional)"]
    }
  ],
  "experience": [
    {
      "company": "string",
      "title": "string",
      "location": "string (optional)",
      "start_date": "string (YYYY-MM)",
      "end_date": "string (YYYY-MM or 'Present')",
      "responsibilities": ["string"],
      "achievements": ["string (optional)"]
    }
  ],
  "skills": {
    "technical": ["string"],
    "soft": ["string (optional)"],
    "languages": ["string (optional)"]
  },
  "projects": [
    {
      "name": "string",
      "description": "string",
      "technologies": ["string"],
      "url": "string (optional)",
      "start_date": "string (YYYY-MM) (optional)",
      "end_date": "string (YYYY-MM or 'Present') (optional)"
    }
  ],
  "certifications": [
    {
      "name": "string",
      "issuer": "string",
      "date": "string (YYYY-MM)",
      "url": "string (optional)"
    }
  ],
  "theme": "string (classic|modern|minimal|professional|creative)"
}
```

## Available Templates

### 1. Classic Template
- Traditional resume layout
- Clean and professional design
- Suitable for most industries
- Features:
  - Serif fonts
  - Traditional section layout
  - Subtle borders and separators

### 2. Modern Template
- Contemporary design with cards
- Accent colors and modern typography
- Perfect for tech and creative industries
- Features:
  - Sans-serif fonts
  - Card-based layout
  - Accent colors
  - Modern spacing

### 3. Minimal Template
- Clean and simple design
- Focus on content
- Ideal for minimalist preferences
- Features:
  - Minimal styling
  - Generous white space
  - Simple typography

### 4. Professional Template
- Corporate-focused design
- Strong emphasis on experience
- Suitable for business and finance
- Features:
  - Professional color scheme
  - Structured layout
  - Clear hierarchy

### 5. Creative Template
- Unique and eye-catching design
- Perfect for creative industries
- Features:
  - Custom color schemes
  - Creative layouts
  - Visual elements

## Dynamic Fields

### Personal Information
- All fields are optional except name and email
- Additional fields can be added:
  - Social media profiles
  - Portfolio links
  - Professional summary

### Education
- Multiple education entries supported
- Dynamic fields:
  - GPA (optional)
  - Course list
  - Achievements
  - Custom date formats

### Experience
- Unlimited experience entries
- Dynamic fields:
  - Company details
  - Role information
  - Responsibilities
  - Achievements
  - Custom date formats

### Skills
- Categorized skills:
  - Technical skills
  - Soft skills
  - Languages
- Custom categories can be added

### Projects
- Multiple project entries
- Dynamic fields:
  - Project details
  - Technologies used
  - Links
  - Timeline

### Certifications
- Optional section
- Dynamic fields:
  - Certification details
  - Issuing organization
  - Dates
  - Verification links

## Theme Customization

Each template supports customization of:
- Color schemes
- Font families
- Spacing
- Layout options
- Section ordering

## API Integration

### Create Resume
```http
POST /api/create-resume
Content-Type: application/json

{
  "resume_data": {
    // Resume structure as defined above
  },
  "theme": "string"
}
```

### Get Preview
```http
GET /api/resume-preview/{resume_id}
```

### Download PDF
```http
GET /api/download-resume/{resume_id}
```

### Get Available Themes
```http
GET /api/themes
```

## Best Practices

1. **Content Organization**
   - Keep descriptions concise
   - Use bullet points for readability
   - Highlight achievements with metrics

2. **Template Selection**
   - Choose template based on industry
   - Consider ATS compatibility
   - Maintain consistency

3. **Data Validation**
   - Required fields must be filled
   - Dates in correct format
   - URLs must be valid

4. **Performance**
   - Optimize images
   - Minimize custom styling
   - Cache generated PDFs

## Error Handling

Common error codes:
- 400: Invalid resume data
- 404: Resume not found
- 500: Server error

## Security

- All API endpoints require authentication
- Resume data is encrypted
- PDFs are generated securely
- Temporary files are cleaned up 