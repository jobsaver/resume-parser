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
        dict: Structured resume data and raw content
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists() and not text_content:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Use provided text content or handle as empty
    if text_content is None:
        text_content = ""
        print("No text content provided, using fallback empty string")
    
    # Extract only basic information from text
    data = {}
    
    # Extract name
    name_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    name_match = re.search(name_pattern, text_content.strip())
    if name_match:
        data['name'] = name_match.group(1).strip()
    else:
        # Try to extract name using NLTK NER
        try:
            first_paragraph = text_content.split('\n\n')[0]
            tokens = word_tokenize(first_paragraph)
            tagged = pos_tag(tokens)
            entities = ne_chunk(tagged)
            
            names = []
            for chunk in entities:
                if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                    names.append(' '.join(c[0] for c in chunk))
            
            if names:
                data['name'] = names[0]
        except Exception as e:
            print(f"Name extraction failed: {str(e)}")
    
    # Extract email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text_content)
    if email_match:
        data['email'] = email_match.group(0)
    
    # Extract phone number
    phone_pattern = r'(?:\+\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}|\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b'
    phone_match = re.search(phone_pattern, text_content)
    if phone_match:
        data['phone'] = phone_match.group(0)
    
    # Extract skills using spaCy if available
    skills = []
    if 'SPACY_AVAILABLE' in globals() and SPACY_AVAILABLE:
        try:
            doc = nlp(text_content)
            
            # Extract noun phrases as potential skills
            for chunk in doc.noun_chunks:
                # Filter out common non-skill noun phrases (like "I", "me", etc.)
                if len(chunk.text.strip()) > 2 and not chunk.text.lower() in ['i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our']:
                    skills.append(chunk.text.strip())
            
            # Extract technical terms (proper nouns and nouns that could be skills)
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2:
                    if token.text.strip() not in skills and not token.text.lower() in ['i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our']:
                        skills.append(token.text.strip())
            
            # Clean and deduplicate skills
            cleaned_skills = []
            for skill in skills:
                # Normalize skill text
                clean_skill = re.sub(r'\s+', ' ', skill).strip()
                if clean_skill and clean_skill.lower() not in [s.lower() for s in cleaned_skills]:
                    cleaned_skills.append(clean_skill)
            
            data['skills'] = cleaned_skills
        except Exception as e:
            print(f"spaCy skill extraction failed: {str(e)}")
    
    # If spaCy is not available, use regex to find skills
    if 'skills' not in data or not data['skills']:
        # Look for skills based on linguistic patterns
        skills_pattern = r'(?:proficient in|experienced with|knowledge of|skilled in|expertise in|familiar with|competent in)\s+((?:[A-Za-z0-9#+.\-]+(?:\s+and\s+|\s*,\s*|\s+)?)+)'
        skills_matches = re.finditer(skills_pattern, text_content, re.IGNORECASE)
        
        # Extract skills from matches
        all_skills = []
        for match in skills_matches:
            skill_text = match.group(1).strip()
            # Split by common separators
            for skill in re.split(r'\s*(?:,|\band\b)\s*', skill_text):
                if skill and len(skill) > 2:  # Avoid very short "skills"
                    all_skills.append(skill.strip())
        
        data['skills'] = list(set(all_skills))
    
    # Extract education, experience and certifications sections
    sections = {}
    section_headers = [
        "education", "experience", "work experience", "employment", 
        "certifications", "certification", "certificates"
    ]
    
    lines = text_content.split('\n')
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
    if 'education' in sections:
        data['education'] = sections['education']
    
    if any(exp in sections for exp in ['experience', 'work experience', 'employment']):
        exp_key = next((k for k in ['experience', 'work experience', 'employment'] if k in sections), None)
        if exp_key:
            data['experience'] = sections[exp_key]
    
    if any(cert in sections for cert in ['certifications', 'certification', 'certificates']):
        cert_key = next((k for k in ['certifications', 'certification', 'certificates'] if k in sections), None)
        if cert_key:
            data['certifications'] = sections[cert_key]
    
    # Clean all text sections
    for key in data:
        if isinstance(data[key], list) and all(isinstance(item, str) for item in data[key]):
            # Clean each item in the list
            cleaned_list = []
            for item in data[key]:
                # Remove unnecessary spaces
                cleaned_item = re.sub(r'\s+', ' ', item).strip()
                if cleaned_item:
                    cleaned_list.append(cleaned_item)
            data[key] = cleaned_list
    
    # Add raw content to the response
    data['raw_content'] = text_content
    
    return data

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