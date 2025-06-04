import re

SECTION_HEADERS = {
    "contact": ["contact", "personal information", "phone", "email"],
    "summary": ["summary", "objective", "profile", "about me", "career summary", "professional summary", "career objective", "summary statement"],
    "experience": ["experience", "work history", "employment", "work experience", "professional experience"],
    "education": ["education", "academic background", "qualifications", "academic qualifications"],
    "skills": ["skills", "technical skills", "soft skills", "core competencies", "areas of expertise", "skills summary", "skills & interests", "skill set", "key skills"],
    "certifications": ["certifications", "licenses", "certificates", "professional certifications", "professional licenses", "certification"],
    "projects": ["projects", "personal projects", "technical projects", "academic projects", "project"],
    "achievements": ["achievements", "awards", "honors", "recognitions", "accomplishments", "technical achievements", "professional achievements", "notable achievements", "key achievements"],
    "strengths": ["strengths", "key strengths", "personal strengths", "professional strengths", "core strengths"],
    "extracurricular": ["extracurricular", "activities", "volunteer", "hobbies", "leadership", "leadership / extracurricular", "co-curricular activities"],
    "responsibilities": ["responsibilities", "duties", "tasks", "positions of responsibility", "por"],
    "interests": ["interests", "hobbies", "passions"],
    "publications": ["publications", "research papers", "journals"],
    "references": ["references", "referees", "recommendations"],
    "objective": ["objective", "career goal", "goal"]
    # "languages": ["languages", "spoken languages", "language proficiency"],
}

def detect_section_positions(resume_text):
    lines = resume_text.split('\n')
    section_positions = {}

    for idx, line in enumerate(lines):
        clean_line = line.strip().lower()

        for section, keywords in SECTION_HEADERS.items():
            for keyword in keywords:
                if re.fullmatch(rf"{keyword}[\s:]*", clean_line):
                    if section not in section_positions:
                        section_positions[section] = idx
    return section_positions, lines

def extract_sections(resume_text):
    section_positions, lines = detect_section_positions(resume_text)

    # Sort sections by appearance
    ordered_sections = sorted(section_positions.items(), key=lambda x: x[1])
    section_texts = {}

    # Extract section content
    for i, (section, start_idx) in enumerate(ordered_sections):
        end_idx = ordered_sections[i + 1][1] if i + 1 < len(ordered_sections) else len(lines)
        section_content = "\n".join(lines[start_idx + 1:end_idx]).strip()
        section_texts[section] = section_content.strip()

    # 🔍 Fallback: If 'contact' section not found, extract everything before first section
    if "contact" not in section_texts and ordered_sections:
        first_section_start = ordered_sections[0][1]
        possible_contact = "\n".join(lines[:first_section_start]).strip()
        if possible_contact:
            section_texts["contact"] = possible_contact

    return section_texts