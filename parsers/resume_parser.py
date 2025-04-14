"""
Resume parser module using regex and NLTK for basic NLP.
This module provides functionality to extract structured information from resume text.
"""
import os
import re
import nltk
import string
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher

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
from nltk.util import ngrams

# Try to import sklearn for text clustering, but don't fail if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: scikit-learn not installed. Advanced text clustering disabled.")

# Try to import spaCy for advanced NLP, but don't fail if not available
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        nlp = spacy.blank("en")
    SPACY_AVAILABLE = True
    print("spaCy loaded successfully for enhanced entity recognition")
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not installed. Advanced entity recognition disabled.")

# Try to import Gensim for topic modeling, but don't fail if not available
try:
    import gensim
    from gensim import corpora
    from gensim.models import LdaModel
    GENSIM_AVAILABLE = True
    print("Gensim loaded successfully for topic modeling")
except ImportError:
    GENSIM_AVAILABLE = False
    print("Warning: gensim not installed. Topic modeling disabled.")

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
    
    # Dynamic field extraction for additional fields not explicitly defined
    # Only use if text content is substantial
    if len(text_content) > 200:
        try:
            dynamic_fields = extract_dynamic_fields(text_content)
            if dynamic_fields:
                manual_data['dynamic_fields'] = dynamic_fields
        except Exception as e:
            print(f"Warning: Dynamic field extraction failed: {str(e)}")
    
    # Clean up the data
    result = clean_parsed_data(manual_data)
    
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
    
    # Extract phone number (improved pattern for international formats)
    phone_pattern = r'(?:\+\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}|\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        result['phone'] = phone_match.group(0)
    
    # Extract LinkedIn profile
    linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile/view\?id=|linkedin\.com/pub/)([a-zA-Z0-9_-]+)'
    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        result['linkedin'] = "linkedin.com/in/" + linkedin_match.group(1)
    
    # Extract websites/portfolio
    website_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})(?:/\S*)?'
    website_matches = re.finditer(website_pattern, text)
    websites = []
    for match in website_matches:
        site = match.group(0)
        # Exclude email domains and linkedin
        if '@' not in site and 'linkedin.com' not in site:
            websites.append(site)
    if websites:
        result['websites'] = websites[:3]  # Limit to first 3 websites
    
    # Extract location/address
    address_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2})\b'
    address_match = re.search(address_pattern, text)
    if address_match:
        result['location'] = address_match.group(0)
    
    # Extract skills using keyword matching
    skills = []
    
    # Common programming languages and technologies
    tech_skills = [
        # Programming Languages
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Swift", "Go", "Rust", "Kotlin",
        "Scala", "R", "Matlab", "Perl", "Shell", "Bash", "PowerShell", "Assembly", "Fortran", "COBOL", "Lisp", "Haskell",
        
        # Web Development
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring", "Express", "ASP.NET", "Ruby on Rails",
        "Laravel", "Symfony", "jQuery", "Redux", "Next.js", "Gatsby", "REST API", "GraphQL", "WebSockets",
        "HTML", "CSS", "SASS", "LESS", "Bootstrap", "Tailwind", "Material UI", "Chakra UI", "Semantic UI",
        
        # Databases
        "SQL", "NoSQL", "MongoDB", "MySQL", "PostgreSQL", "Oracle", "SQLite", "Firebase", "DynamoDB", "Cassandra",
        "Redis", "Elasticsearch", "Couchbase", "MariaDB", "Neo4j", "GraphDB", "MS SQL Server",
        
        # Cloud & DevOps
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Jenkins", "Travis CI", "CircleCI", "GitHub Actions",
        "Terraform", "Ansible", "Puppet", "Chef", "Nginx", "Apache", "Load Balancing", "Serverless", "Lambda",
        "Microservices", "ECS", "EKS", "EC2", "S3", "CloudFront", "IAM", "VPC", "Heroku", "DigitalOcean",
        
        # Data Science & AI
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Data Science", "SciPy", "Keras", "NLTK", "spaCy",
        "Machine Learning", "AI", "NLP", "Computer Vision", "Deep Learning", "Data Mining", "Big Data", "Spark",
        "Hadoop", "ETL", "Data Warehousing", "Data Modeling", "Statistical Analysis", "Regression", "Classification",
        "Clustering", "Neural Networks", "Reinforcement Learning", "Genetic Algorithms", "OpenCV",
        
        # Mobile Development
        "iOS", "Android", "React Native", "Flutter", "Xamarin", "Swift UI", "Kotlin", "Jetpack Compose", "Mobile App",
        "Objective-C", "ARKit", "CoreML", "Push Notifications", "Mobile UI/UX",
        
        # Testing & QA
        "JUnit", "TestNG", "Selenium", "Cypress", "Jest", "Mocha", "Chai", "Pytest", "RSpec", "Test Automation",
        "TDD", "BDD", "Unit Testing", "Integration Testing", "E2E Testing", "Load Testing", "Performance Testing",
        "Postman", "Quality Assurance"
    ]
    
    # Business skills for all industries
    business_skills = [
        # Project Management
        "Project Management", "Agile", "Scrum", "Kanban", "Waterfall", "JIRA", "Confluence", "Trello", "Asana",
        "MS Project", "PMP", "PRINCE2", "Six Sigma", "Lean", "Sprint Planning", "Backlog Grooming", "Stand-ups",
        
        # Business/Management
        "Leadership", "Team Management", "Strategic Planning", "Business Analysis", "Product Management",
        "Operations Management", "Supply Chain", "Procurement", "Logistics", "Change Management",
        "Risk Management", "Stakeholder Management", "Budget Management", "Forecasting", "KPI",
        "Performance Management", "Team Building", "Mentoring", "Coaching", "Delegation", "Process Improvement",
        
        # Finance/Accounting
        "Financial Analysis", "Accounting", "Budgeting", "Cost Analysis", "Financial Reporting", "Financial Modeling",
        "Forecasting", "Revenue Management", "P&L", "Balance Sheet", "Cash Flow", "ROI Analysis", "QuickBooks",
        "SAP", "Oracle Financials", "Excel", "Financial Planning", "Tax", "Audit", "CPA", "GAAP", "IFRS",
        
        # Marketing/Sales
        "Digital Marketing", "SEO", "SEM", "Content Marketing", "Social Media Marketing", "Email Marketing",
        "Marketing Strategy", "Brand Management", "Market Research", "Customer Acquisition", "CRM", "Salesforce",
        "HubSpot", "Google Analytics", "Google Ads", "Facebook Ads", "Marketing Automation", "Sales Management",
        "Business Development", "Account Management", "Customer Success", "Lead Generation", "Negotiation",
        
        # Healthcare
        "Electronic Health Records", "EHR", "EMR", "Epic", "Cerner", "HIPAA", "Patient Care", "Clinical Documentation",
        "Medical Coding", "Medical Billing", "Clinical Research", "Pharmaceuticals", "Telemedicine", "Healthcare Administration",
        
        # Legal
        "Contract Law", "Compliance", "Regulatory Affairs", "GDPR", "Intellectual Property", "Legal Research",
        "Case Management", "Due Diligence", "Corporate Law", "Litigation", "Arbitration", "Legal Writing",
        
        # Human Resources
        "HR Management", "Talent Acquisition", "Recruiting", "Onboarding", "Employee Relations", "Compensation",
        "Benefits Administration", "Performance Reviews", "HRIS", "Workday", "ADP", "Payroll", "HR Compliance",
        "Diversity & Inclusion", "Workforce Planning", "Employee Engagement", "Training & Development", "Succession Planning",
        
        # Design & Creative
        "UX/UI Design", "Graphic Design", "Adobe Creative Suite", "Photoshop", "Illustrator", "InDesign", "Figma", "Sketch",
        "Wireframing", "Prototyping", "User Research", "User Testing", "Visual Design", "Brand Identity", "Typography",
        "Color Theory", "Animation", "Video Editing", "3D Modeling", "Motion Graphics", "Web Design", "Responsive Design",
        
        # Education
        "Curriculum Development", "Instructional Design", "E-Learning", "LMS", "Teaching", "Training", "Assessment",
        "Educational Technology", "Student Engagement", "Learning Outcomes", "Course Management", "Blackboard", "Canvas",
        
        # Communication
        "Written Communication", "Verbal Communication", "Presentation Skills", "Public Speaking", "Technical Writing",
        "Report Writing", "Business Writing", "Copywriting", "Content Creation", "Editing", "Proofreading", "Storytelling",
        "Cross-functional Communication", "Client Communication", "Executive Communication"
    ]
    
    # Industry-specific skills
    industry_skills = [
        # Manufacturing/Engineering
        "CAD", "AutoCAD", "SolidWorks", "CATIA", "3D Modeling", "Manufacturing Processes", "Quality Control",
        "Six Sigma", "Lean Manufacturing", "CNC Programming", "GD&T", "PLC", "SCADA", "Industrial Automation",
        "Process Engineering", "Manufacturing Engineering", "Mechanical Engineering", "Electrical Engineering",
        "Civil Engineering", "Chemical Engineering", "Industrial Engineering", "Systems Engineering", "IoT",
        "Robotics", "PCB Design", "Circuit Design", "HVAC", "Welding", "Machining", "ISO 9001",
        
        # Finance/Banking
        "Investment Banking", "Portfolio Management", "Asset Management", "Wealth Management", "Risk Assessment",
        "Derivatives", "Fixed Income", "Equities", "Financial Regulations", "AML", "KYC", "Bloomberg Terminal",
        "CFA", "Financial Modeling", "Valuation", "M&A", "Private Equity", "Venture Capital", "Hedge Funds",
        "Credit Analysis", "Underwriting", "Mortgage Lending", "Retail Banking", "Commercial Banking",
        
        # Healthcare/Medical
        "Patient Care", "Clinical Trials", "Nursing", "Physician", "Medical Devices", "Biotechnology", "Pharmacology",
        "Healthcare Compliance", "Medical Research", "Public Health", "Epidemiology", "Radiology", "Surgery",
        "Mental Health", "Physical Therapy", "Occupational Therapy", "Speech Therapy", "Telehealth",
        
        # Retail/Consumer
        "Merchandising", "Inventory Management", "POS Systems", "Retail Operations", "E-commerce", "Omnichannel",
        "Category Management", "Pricing Strategy", "Vendor Management", "Customer Experience", "Visual Merchandising",
        "Retail Analytics", "Forecasting", "Demand Planning", "Consumer Insights", "Brand Development",
        
        # Energy/Utilities
        "Renewable Energy", "Solar", "Wind", "Hydroelectric", "Oil & Gas", "Petroleum Engineering", "Power Generation",
        "Transmission", "Distribution", "Energy Efficiency", "Smart Grid", "Utility Regulations", "Energy Trading",
        "Environmental Compliance", "Sustainability", "Carbon Footprint", "Energy Modeling", "LEED", "Green Building",
        
        # Government/Public Sector
        "Public Policy", "Public Administration", "Government Contracting", "Grant Management", "Legislative Process",
        "Regulatory Compliance", "Policy Analysis", "Foreign Affairs", "Diplomacy", "National Security",
        "Defense", "Intelligence Analysis", "Emergency Management", "Disaster Recovery", "Urban Planning"
    ]
    
    # Combine all skills lists
    all_skills = tech_skills + business_skills + industry_skills
    
    # Find skills in the resume text
    for skill in all_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            skills.append(skill)
    
    result['skills'] = list(set(skills))
    
    # Identify industry from text
    industries = [
        "Technology", "Software", "IT", "Financial Services", "Banking", "Insurance", "Healthcare", 
        "Medical", "Pharmaceutical", "Manufacturing", "Engineering", "Construction", "Retail", 
        "E-commerce", "Consulting", "Professional Services", "Education", "Government", 
        "Non-profit", "Media", "Entertainment", "Telecommunications", "Energy", "Oil & Gas", 
        "Transportation", "Logistics", "Hospitality", "Food & Beverage", "Real Estate", 
        "Agriculture", "Automotive"
    ]
    
    identified_industries = []
    for industry in industries:
        if re.search(r'\b' + re.escape(industry) + r'\b', text, re.IGNORECASE):
            identified_industries.append(industry)
    
    if identified_industries:
        result['industry'] = identified_industries
    
    # Extract dates for timeline analysis
    date_pattern = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\s*[-–—]?\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\s*[-–—]?\s*Present|Current)\b'
    date_matches = re.finditer(date_pattern, text, re.IGNORECASE)
    date_entries = [match.group(0) for match in date_matches]
    if date_entries:
        result['timeline'] = date_entries
    
    # Extract years of experience
    exp_pattern = r'(\d+)\+?\s*years?\s*(of)?\s*experience'
    exp_match = re.search(exp_pattern, text, re.IGNORECASE)
    if exp_match:
        try:
            result['years_of_experience'] = int(exp_match.group(1))
        except:
            pass
    
    # Extract job titles
    job_titles = [
        "Software Engineer", "Product Manager", "Project Manager", "Data Scientist", "Data Analyst",
        "Business Analyst", "Financial Analyst", "Marketing Manager", "Sales Manager", "Operations Manager",
        "CEO", "CTO", "CFO", "CIO", "COO", "Director", "VP", "Vice President", "Senior", "Junior",
        "Lead", "Head", "Chief", "Manager", "Supervisor", "Coordinator", "Specialist", "Consultant",
        "Analyst", "Engineer", "Developer", "Designer", "Architect", "Administrator", "Technician"
    ]
    
    found_titles = []
    for title in job_titles:
        if re.search(r'\b' + re.escape(title) + r'\b', text, re.IGNORECASE):
            # Get the complete job title (including words before and after)
            matches = re.finditer(r'([A-Z][a-z]+\s+)*\b' + re.escape(title) + r'\b(\s+[A-Z][a-z]+)*', text)
            for match in matches:
                found_titles.append(match.group(0).strip())
    
    if found_titles:
        result['job_titles'] = list(set(found_titles))
    
    # Extract sections
    sections = {}
    section_headers = [
        "education", "experience", "work experience", "employment", "skills", 
        "projects", "certifications", "achievements", "awards", "publications",
        "summary", "objective", "professional summary", "profile", "about",
        "languages", "volunteer", "interests", "activities", "references"
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
    if 'summary' in sections or 'profile' in sections or 'about' in sections or 'objective' in sections or 'professional summary' in sections:
        key = next((k for k in ['summary', 'profile', 'about', 'objective', 'professional summary'] if k in sections), None)
        if key:
            result['summary'] = ' '.join(sections[key])
    
    if 'education' in sections:
        result['education'] = sections['education']
    
    if any(exp in sections for exp in ['experience', 'work experience', 'employment']):
        exp_key = next(k for k in ['experience', 'work experience', 'employment'] if k in sections)
        result['experience'] = sections[exp_key]
    
    if 'projects' in sections:
        result['projects'] = sections['projects']
    
    if 'certifications' in sections:
        result['certifications'] = sections['certifications']
    
    if 'achievements' in sections or 'awards' in sections:
        key = next((k for k in ['achievements', 'awards'] if k in sections), None)
        if key:
            result['achievements'] = sections[key]
    
    if 'publications' in sections:
        result['publications'] = sections['publications']
    
    if 'languages' in sections:
        result['languages'] = sections['languages']
    
    if 'volunteer' in sections:
        result['volunteer'] = sections['volunteer']
    
    # Clean all text sections
    for key in result:
        if isinstance(result[key], list) and all(isinstance(item, str) for item in result[key]):
            # Clean each item in the list
            cleaned_list = []
            for item in result[key]:
                # Remove unnecessary spaces
                cleaned_item = re.sub(r'\s+', ' ', item).strip()
                if cleaned_item:
                    cleaned_list.append(cleaned_item)
            result[key] = cleaned_list
    
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

def extract_dynamic_fields(text):
    """
    Extract dynamic fields from resume text that aren't explicitly defined
    
    Args:
        text (str): The text content of the resume
        
    Returns:
        dict: Dynamically extracted fields
    """
    if not text:
        return {}
    
    dynamic_fields = {}
    
    # 1. Extract potential custom sections using pattern recognition
    try:
        custom_sections = detect_custom_sections(text)
        if custom_sections:
            dynamic_fields['custom_sections'] = custom_sections
    except Exception as e:
        print(f"Custom section detection failed: {str(e)}")
    
    # 2. Extract potential key-value pairs
    try:
        key_value_pairs = extract_key_value_pairs(text)
        if key_value_pairs:
            dynamic_fields['key_value_pairs'] = key_value_pairs
    except Exception as e:
        print(f"Key-value extraction failed: {str(e)}")
    
    # 3. Extract domain-specific terminology
    try:
        domain_terms = extract_domain_terminology(text)
        if domain_terms:
            dynamic_fields['domain_terminology'] = domain_terms
    except Exception as e:
        print(f"Domain terminology extraction failed: {str(e)}")
    
    # 4. Apply text clustering if scikit-learn is available
    if ML_AVAILABLE and len(text) > 500:  # Only for substantial text
        try:
            clusters = cluster_text_segments(text)
            if clusters:
                dynamic_fields['content_clusters'] = clusters
        except Exception as e:
            print(f"Text clustering failed: {str(e)}")
    
    # 5. Extract named entities using spaCy if available
    if 'SPACY_AVAILABLE' in globals() and SPACY_AVAILABLE and len(text) > 200:
        try:
            entities = extract_spacy_entities(text)
            if entities:
                dynamic_fields['entities'] = entities
        except Exception as e:
            print(f"spaCy entity extraction failed: {str(e)}")
    
    # 6. Apply topic modeling if Gensim is available
    if 'GENSIM_AVAILABLE' in globals() and GENSIM_AVAILABLE and len(text) > 500:
        try:
            topics = extract_topics(text)
            if topics:
                dynamic_fields['topics'] = topics
        except Exception as e:
            print(f"Topic modeling failed: {str(e)}")
    
    return dynamic_fields

def detect_custom_sections(text):
    """
    Detect custom sections in the resume that don't match standard sections
    
    Args:
        text (str): Resume text content
        
    Returns:
        dict: Custom sections with their content
    """
    standard_sections = [
        "education", "experience", "work experience", "employment", "skills", 
        "projects", "certifications", "achievements", "awards", "publications",
        "summary", "objective", "professional summary", "profile", "about",
        "languages", "volunteer", "interests", "activities", "references",
        "contact", "contact information", "personal information", "qualification"
    ]
    
    # Look for lines that appear to be section headers
    section_pattern = r'^[A-Z][A-Za-z\s]+:?$'
    lines = text.split('\n')
    
    custom_sections = {}
    current_section = None
    section_content = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check if this line looks like a section header
        if re.match(section_pattern, line):
            # Clean the section name
            section_name = line.rstrip(':').strip().lower()
            
            # Save previous section if exists
            if current_section and section_content:
                custom_sections[current_section] = section_content
                section_content = []
            
            # Check if this is a standard section
            is_standard = any(standard == section_name or standard in section_name or section_name in standard 
                              for standard in standard_sections)
            
            if not is_standard:
                current_section = section_name
            else:
                current_section = None
        
        # Add content to current custom section
        elif current_section and line:
            section_content.append(line)
    
    # Add the last section if it exists
    if current_section and section_content:
        custom_sections[current_section] = section_content
    
    return custom_sections

def extract_key_value_pairs(text):
    """
    Extract key-value pairs from resume text
    
    Args:
        text (str): Resume text content
        
    Returns:
        dict: Extracted key-value pairs
    """
    # Patterns for key-value pairs
    kv_patterns = [
        r'([A-Za-z\s]+):\s*([^:\n]+)',  # Standard key: value format
        r'([A-Za-z\s]+)\s*-\s*([^-\n]+)'  # Key - value format
    ]
    
    pairs = {}
    
    for pattern in kv_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            key = match.group(1).strip().lower()
            value = match.group(2).strip()
            
            # Skip if key contains common words that are likely not real keys
            if key in ['and', 'the', 'for', 'with', 'from', 'to']:
                continue
                
            # Skip if key is longer than 30 characters (likely not a real key)
            if len(key) > 30:
                continue
                
            # Skip pairs with empty values
            if not value:
                continue
                
            # Convert known numeric values
            if key in ['age', 'years', 'salary', 'gpa', 'score']:
                try:
                    value = float(re.search(r'\d+(\.\d+)?', value).group(0))
                except:
                    pass
            
            pairs[key] = value
    
    return pairs

def extract_domain_terminology(text):
    """
    Extract domain-specific terminology using NLP techniques
    
    Args:
        text (str): Resume text content
        
    Returns:
        list: Domain-specific terms
    """
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text.lower())
    
    # Get POS tags
    tagged_words = pos_tag(words)
    
    # Extract noun phrases (potential domain terms)
    noun_phrases = []
    for i, (word, tag) in enumerate(tagged_words):
        # Skip stop words and punctuation
        if word in stop_words or word in string.punctuation:
            continue
            
        # Look for noun phrases (noun preceded by adjectives)
        if tag.startswith('NN'):  # Noun
            phrase = [word]
            
            # Look backward for adjectives
            j = i - 1
            while j >= 0 and tagged_words[j][1].startswith('JJ') and j > i - 3:
                phrase.insert(0, tagged_words[j][0])
                j -= 1
                
            if len(phrase) > 1:  # Only multi-word phrases
                noun_phrases.append(' '.join(phrase))
    
    # Extract technical bigrams and trigrams
    tokens = [w for w in words if w not in stop_words and w not in string.punctuation]
    bi_grams = list(ngrams(tokens, 2))
    tri_grams = list(ngrams(tokens, 3))
    
    bi_gram_phrases = [' '.join(g) for g in bi_grams]
    tri_gram_phrases = [' '.join(g) for g in tri_grams]
    
    # Combine all potential domain terms
    all_terms = noun_phrases + bi_gram_phrases + tri_gram_phrases
    
    # Count frequencies
    term_freq = Counter(all_terms)
    
    # Return terms that appear multiple times (more likely to be domain-specific)
    domain_terms = [term for term, count in term_freq.items() if count > 1]
    
    # Remove similar terms (keep the longer one)
    unique_terms = []
    for term in sorted(domain_terms, key=len, reverse=True):
        if not any(
            term in other_term and term != other_term 
            or SequenceMatcher(None, term, other_term).ratio() > 0.8
            for other_term in unique_terms
        ):
            unique_terms.append(term)
    
    return unique_terms[:20]  # Return top 20 terms

def cluster_text_segments(text):
    """
    Cluster text segments to identify thematic areas
    
    Args:
        text (str): Resume text content
        
    Returns:
        dict: Clusters of text with their themes
    """
    if not ML_AVAILABLE:
        return {}
    
    # Split text into paragraphs
    paragraphs = [p for p in text.split('\n\n') if len(p) > 50]
    
    if len(paragraphs) < 3:  # Need at least 3 paragraphs for meaningful clustering
        return {}
    
    # Vectorize text
    vectorizer = TfidfVectorizer(
        max_features=100, 
        stop_words='english', 
        ngram_range=(1, 2)
    )
    X = vectorizer.fit_transform(paragraphs)
    
    # Determine optimal number of clusters (between 2 and 5)
    n_clusters = min(5, len(paragraphs) - 1)
    n_clusters = max(2, n_clusters)
    
    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)
    
    # Get top terms for each cluster
    terms = vectorizer.get_feature_names_out()
    centroids = kmeans.cluster_centers_
    
    # Organize results
    results = {}
    for i in range(n_clusters):
        # Get top terms for this cluster
        order_centroids = centroids[i].argsort()[::-1]
        cluster_terms = [terms[idx] for idx in order_centroids[:5]]
        
        # Get paragraphs in this cluster
        cluster_paragraphs = [p for j, p in enumerate(paragraphs) if clusters[j] == i]
        
        # Name the cluster based on its terms
        cluster_name = f"Cluster {i+1}: {', '.join(cluster_terms[:3])}"
        results[cluster_name] = cluster_paragraphs
    
    return results

def extract_spacy_entities(text):
    """
    Extract named entities using spaCy
    
    Args:
        text (str): Resume text content
        
    Returns:
        dict: Extracted entities by type
    """
    # Check if spaCy is available
    if 'SPACY_AVAILABLE' not in globals() or not SPACY_AVAILABLE or 'nlp' not in globals():
        print("spaCy not available for entity extraction")
        return {}
    
    try:
        # Process the text with spaCy
        doc = nlp(text)
        
        # Group entities by type
        entities_by_type = {}
        for ent in doc.ents:
            # Skip very short entities (likely noise)
            if len(ent.text) < 3:
                continue
                
            # Clean the entity text
            clean_text = re.sub(r'\s+', ' ', ent.text).strip()
            
            # Skip if empty after cleaning
            if not clean_text:
                continue
                
            # Add to appropriate type
            entity_type = ent.label_
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
                
            # Add if not duplicate
            if clean_text not in entities_by_type[entity_type]:
                entities_by_type[entity_type].append(clean_text)
        
        # Map spaCy entity types to more user-friendly names
        entity_map = {
            'ORG': 'organizations',
            'GPE': 'locations',
            'LOC': 'locations',
            'PERSON': 'people',
            'DATE': 'dates',
            'MONEY': 'financial',
            'PERCENT': 'metrics',
            'PRODUCT': 'products',
            'EVENT': 'events',
            'WORK_OF_ART': 'works',
            'LAW': 'regulations',
            'LANGUAGE': 'languages'
        }
        
        # Rename entity types to be more user-friendly
        friendly_entities = {}
        for entity_type, entities in entities_by_type.items():
            friendly_type = entity_map.get(entity_type, entity_type.lower())
            friendly_entities[friendly_type] = entities
        
        return friendly_entities
    
    except Exception as e:
        print(f"Error in spaCy entity extraction: {str(e)}")
        return {}

def extract_topics(text):
    """
    Extract topics from text using LDA topic modeling
    
    Args:
        text (str): Resume text content
        
    Returns:
        list: Extracted topics with keywords
    """
    # Check if Gensim is available
    if 'GENSIM_AVAILABLE' not in globals() or not GENSIM_AVAILABLE:
        print("Gensim not available for topic modeling")
        return []
    
    try:
        # Preprocess text
        stop_words = set(stopwords.words('english'))
        paragraphs = [p for p in text.split('\n\n') if len(p) > 50]
        
        if len(paragraphs) < 3:  # Need at least 3 paragraphs
            return []
        
        # Tokenize and clean
        tokenized_paragraphs = []
        for paragraph in paragraphs:
            tokens = word_tokenize(paragraph.lower())
            # Remove stopwords, punctuation, and short words
            cleaned_tokens = [
                w for w in tokens 
                if w not in stop_words and w not in string.punctuation and len(w) > 2
            ]
            tokenized_paragraphs.append(cleaned_tokens)
        
        # Create dictionary and corpus
        dictionary = corpora.Dictionary(tokenized_paragraphs)
        corpus = [dictionary.doc2bow(text) for text in tokenized_paragraphs]
        
        # Build LDA model
        num_topics = min(3, len(paragraphs))
        lda_model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            random_state=42,
            passes=10
        )
        
        # Extract topics
        topics = []
        for topic_id, topic_terms in lda_model.print_topics(num_words=5):
            # Extract terms from the topic string
            terms = re.findall(r'"([^"]+)"', topic_terms)
            topics.append({
                'id': topic_id,
                'terms': terms
            })
        
        return topics
    
    except Exception as e:
        print(f"Error in topic modeling: {str(e)}")
        return [] 