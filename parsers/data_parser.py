import re
import json
import spacy

nlp = spacy.load("en_core_web_sm")

def parse_duration(duration_text):
    parts = re.split(r'\s*[-–—]\s*', duration_text)
    start_date = parts[0].strip() if len(parts) > 0 else None
    end_date = parts[1].strip() if len(parts) > 1 else None
    
    if end_date and end_date.lower() in ['present', 'current', 'now']:
        end_date = 'Present'
    
    return start_date, end_date

def structure_experience_spacy(raw_text):
    lines = raw_text.split('\n')

    experiences = []
    exp = {
        "raw_experience": raw_text.strip(),
    }
    experiences.append(exp)
    current_exp = {
        "company": None,
        "title": None,
        "start_date": None,
        "end_date": None,
        "location": None,
        "responsibilities": [],
    }
    start_idx = 0

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        if line.startswith("•"):
            resp = line.lstrip("• ").strip()
            current_exp["responsibilities"].append(resp)
            continue

        sub_doc = nlp(line)
        ents = {ent.label_: ent.text for ent in sub_doc.ents}

        if "ORG" in ents and not current_exp["company"]:
            current_exp["company"] = ents["ORG"]

        if "DATE" in ents and not current_exp["start_date"]:
            start, end = parse_duration(ents["DATE"])
            current_exp["start_date"] = start
            current_exp["end_date"] = end

        if "GPE" in ents and not current_exp["location"]:
            current_exp["location"] = ents["GPE"]

        if re.search(r'\b(Intern|Engineer|Manager|Researcher|Scientist|Analyst|Developer)\b', line, re.IGNORECASE):
            current_exp["title"] = line

        if (
            i + 1 < len(lines) and
            lines[i + 1].strip() and
            not lines[i + 1].startswith("•") and
            current_exp["company"] and current_exp["title"]
        ):
            if current_exp["responsibilities"]:
                experiences.append(current_exp)
            current_exp = {
                "company": None,
                "title": None,
                "start_date": None,
                "end_date": None,
                "location": None,
                "responsibilities": [],
            }
            start_idx = i + 1

    if current_exp["responsibilities"]:
        experiences.append(current_exp)

    ordinal_suffixes = ["0th", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th"]
    structured = {ordinal_suffixes[i]: exp for i, exp in enumerate(experiences)}
    return structured

def parse_skills(skills_string):
    skills_dict = {}
    
    lines = skills_string.strip().split('\n')
    current_category = None
    category_pattern = re.compile(r'^\s*(?:•\s*)?([^:]+?)\s*:\s*(.*)?$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        category_match = category_pattern.match(line)
        if category_match:
            category = category_match.group(1).strip()
            skills = category_match.group(2).strip() if category_match.group(2) else ""
            normalized_category = re.sub(r'\s*&\s*|\s+', '', category)
            skills_dict[normalized_category] = []
            if skills:
                skills_dict[normalized_category] = [skill.strip() for skill in skills.split(',') if skill.strip()]
            current_category = normalized_category
        else:
            if current_category and line.startswith('•'):
                skill_line = re.sub(r'^\s*•\s*', '', line).strip()
                if skill_line:
                    skills_dict[current_category].extend([skill.strip() for skill in skill_line.split(',') if skill.strip()])
    
    skills_dict = {k: v for k, v in skills_dict.items() if v}
    
    return skills_dict

def get_all_skills(skills):
    skills = parse_skills(skills)
    skills_list = []
    if not skills:
        return skills_list
    
    for category, list in skills.items():
        for skill in list:
            if skill not in skills_list:
                skills_list.append(skill)

    return skills_list

def extract_contact_info(contact_string):
    contact_string = re.sub(r'[^\x00-\x7F]+', ' ', contact_string)
    contact_string = re.sub(r'\s+', ' ', contact_string).strip()
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    url_pattern = r'((?:https?://)?[A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/in)?/[A-Za-z0-9-]+)'
    full_phone_pattern = r'(?:\+91[\s\-]?|\(\+91\)\s*|0)?\d{10}'

    emails = re.findall(email_pattern, contact_string)
    phones_full = re.findall(full_phone_pattern, contact_string)
    phones = [re.search(r'\d{10}$', p).group() for p in phones_full]
    phones = list(set(phones))    
    
    profiles = {}
    url_matches = re.findall(url_pattern, contact_string)
    for full_url in url_matches:
        match = re.match(r'(https?://)?([A-Za-z0-9-]+)\.([A-Za-z]{2,})(?:/in)?/([A-Za-z0-9-]+)', full_url)
        if match:
            protocol, platform, domain, profile_id = match.groups()
            standardized_url = full_url if protocol else f'https://{full_url}'
            profiles[platform] = standardized_url

    main_content = contact_string

    for email in emails:
        main_content = main_content.replace(email, '')
    for full_phone in phones_full:
        main_content = main_content.replace(full_phone, '')
    for url in url_matches:
        full_http = url if url.startswith("http") else f'https://{url}'
        main_content = main_content.replace(url, '').replace(full_http, '')

    main_content = re.sub(r'https?://[A-Za-z0-9.-]*/?', '', main_content)
    main_content = re.sub(r'\s+', ' ', main_content).strip()
    main_content = re.sub(r'[#ï§]', '', main_content).strip()

    contact_info = {
        "main": main_content,
        "mails": emails,
        "phone number": phones,
        "profiles": profiles
    }

    return contact_info

def structure_projects(raw_projects_text):
    lines = raw_projects_text.split('\n')
    projects = []
    raw_projects_text = raw_projects_text.strip()
    
    if raw_projects_text:
        current_project = {
            "project_name": "Raw Project Text",
            "tech_stack": [],
            "start_date": None,
            "end_date": None,
            "description": [raw_projects_text]
        }
    else:
        return {"projects": []}
    projects.append(current_project)
    current_project = {
        "project_name": None,
        "tech_stack": [],
        "start_date": None,
        "end_date": None,
        "description": []
    }

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line and ('|' in line or '§' in line):
            if current_project["project_name"]:
                projects.append(current_project)
                current_project = {
                    "project_name": None,
                    "tech_stack": [],
                    "start_date": None,
                    "end_date": None,
                    "description": []
                }

            parts = re.split(r'\s*[|§]\s*', line)
            current_project["project_name"] = parts[0].strip()

            if len(parts) > 1:
                current_project["tech_stack"] = [tech.strip() for tech in parts[1].split(',')]

            if i + 1 < len(lines) and re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}', lines[i + 1], re.IGNORECASE):
                current_project["start_date"] = lines[i + 1].strip()
                current_project["end_date"] = None
                i += 1

        elif line.startswith("•"):
            current_project["description"].append(line.lstrip("• ").strip())

        i += 1

    if current_project["project_name"]:
        projects.append(current_project)

    return projects