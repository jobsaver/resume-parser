"""
Resume parser module using regex and NLTK for basic NLP.
This module provides functionality to extract structured information from resume text.
"""
import os
import re
import nltk
from pathlib import Path

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)

from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag, ne_chunk
from nltk.tree import Tree

def parse_resume(pdf_path, text_content=None):
    """
    Parse a resume PDF file and extract structured information.
    
    Args:
        pdf_path (str or Path): Path to the resume PDF file
        text_content (str, optional): Pre-extracted text content
        
    Returns:
        dict: Structured resume data
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists() and not text_content:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Use provided text content or handle as empty
    if text_content is None:
        text_content = ""
        print("No text content provided, using fallback empty string")
    
    # Manual extraction from text
    manual_data = extract_from_text(text_content)
    
    # Combine results
    result = {
        'name': manual_data.get('name', ''),
        'email': manual_data.get('email', ''),
        'phone': manual_data.get('phone', ''),
        'skills': manual_data.get('skills', []),
        'experience': manual_data.get('experience', []),
        'education': manual_data.get('education', []),
        'summary': manual_data.get('summary', '')
    }
    
    # Clean up the data
    result = clean_parsed_data(result)
    
    return result

def extract_from_text(text):
    """
    Extract information from resume text using regex and NLP
    
    Args:
        text (str): The text content of the resume
        
    Returns:
        dict: Extracted information
    """
    if not text:
        return {}
    
    result = {}
    
    # Extract name (usually at the top)
    name_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    name_match = re.search(name_pattern, text.strip())
    if name_match:
        result['name'] = name_match.group(1).strip()
    else:
        # Try to extract name using NLTK NER
        try:
            first_paragraph = text.split('\n\n')[0]
            tokens = word_tokenize(first_paragraph)
            tagged = pos_tag(tokens)
            entities = ne_chunk(tagged)
            
            names = []
            for chunk in entities:
                if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                    names.append(' '.join(c[0] for c in chunk))
            
            if names:
                result['name'] = names[0]
        except Exception as e:
            print(f"Name extraction failed: {str(e)}")
    
    # Extract email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text)
    if email_match:
        result['email'] = email_match.group(0)
    
    # Extract phone number
    phone_pattern = r'(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        result['phone'] = phone_match.group(0)
    
    # Extract skills using keyword matching
    skills = []
    
    # Common programming languages and technologies
    tech_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Swift",
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring", "Express",
        "SQL", "NoSQL", "MongoDB", "MySQL", "PostgreSQL", "Oracle", "GraphQL",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Jenkins", "Git",
        "HTML", "CSS", "SASS", "LESS", "Bootstrap", "Tailwind", "Material UI",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Data Science",
        "Machine Learning", "AI", "NLP", "Computer Vision", "Deep Learning"
    ]
    
    for skill in tech_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            skills.append(skill)
    
    result['skills'] = list(set(skills))
    
    # Extract sections
    sections = {}
    section_headers = [
        "education", "experience", "work experience", "employment", "skills", 
        "projects", "certifications", "achievements", "summary", "objective"
    ]
    
    lines = text.split('\n')
    current_section = None
    for line in lines:
        # Check if this line is a section header
        for header in section_headers:
            if re.search(r'\b' + re.escape(header) + r'\b', line, re.IGNORECASE):
                current_section = header.lower()
                sections[current_section] = []
                break
        
        # Add content to current section
        if current_section and line.strip() and not any(h in line.lower() for h in section_headers):
            sections[current_section].append(line.strip())
    
    # Process sections
    if 'summary' in sections:
        result['summary'] = ' '.join(sections['summary'])
    
    if 'education' in sections:
        result['education'] = sections['education']
    
    if any(exp in sections for exp in ['experience', 'work experience', 'employment']):
        exp_key = next(k for k in ['experience', 'work experience', 'employment'] if k in sections)
        result['experience'] = sections[exp_key]
    
    return result

def clean_parsed_data(data):
    """
    Clean and normalize the parsed resume data
    
    Args:
        data (dict): Raw parsed data
        
    Returns:
        dict: Cleaned data
    """
    # Ensure all fields exist
    result = {
        'name': '',
        'email': '',
        'phone': '',
        'skills': [],
        'experience': [],
        'education': [],
        'summary': ''
    }
    
    # Update with existing data
    result.update(data)
    
    # Clean skills (remove duplicates and normalize)
    if result['skills']:
        # Convert to lowercase for comparison
        skills_lower = [skill.lower() for skill in result['skills']]
        # Remove duplicates while preserving order
        unique_skills = []
        for skill in result['skills']:
            if skill.lower() not in [s.lower() for s in unique_skills]:
                unique_skills.append(skill)
        result['skills'] = unique_skills
    
    # Clean experience and education (ensure they're lists of strings)
    for field in ['experience', 'education']:
        if not isinstance(result[field], list):
            if result[field]:
                result[field] = [str(result[field])]
            else:
                result[field] = []
    
    return result 