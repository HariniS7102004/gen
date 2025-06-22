import os
import json
import re
from typing import Dict, List, Any, Optional
import PyPDF2
import docx
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ResumeExtracter:
    def __init__(self):
        """Initialize the resume parser with regex patterns"""
        self.setup_patterns()
        
    def setup_patterns(self):
        """Setup regex patterns for extraction"""
        # Common name patterns - usually appear at the top of resume
        self.name_patterns = [
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\s*$',  # Full name on a line
            r'^([A-Z][A-Z\s]+)$',  # All caps name
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s*\n|$)',  # Name at start of line
        ]
        
        # Professional title patterns
        self.title_patterns = [
            r'(?i)\b(software\s+(?:engineer|developer|architect|lead|manager))',
            r'(?i)\b(data\s+(?:scientist|analyst|engineer))',
            r'(?i)\b(product\s+(?:manager|owner|lead))',
            r'(?i)\b(full\s+stack\s+developer)',
            r'(?i)\b(web\s+developer)',
            r'(?i)\b(mobile\s+(?:developer|engineer))',
            r'(?i)\b(devops\s+engineer)',
            r'(?i)\b(machine\s+learning\s+engineer)',
            r'(?i)\b(backend\s+developer)',
            r'(?i)\b(frontend\s+developer)',
            r'(?i)\b(quality\s+assurance\s+engineer)',
            r'(?i)\b(business\s+analyst)',
            r'(?i)\b(project\s+manager)',
            r'(?i)\b(senior|junior|lead|principal|staff)\s+\w+',
        ]
        
        # Location patterns
        self.location_patterns = [
            r'([A-Z][a-z]+),\s*([A-Z]{2}|\b[A-Z][a-z]+\b)(?:,\s*([A-Z][a-z\s]+))?',  # City, State/Province, Country
            r'([A-Z][a-z\s]+),\s*([A-Z][a-z\s]+)',  # City, Country
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d{5}(?:-\d{4})?)\b',  # City, ZIP
        ]
        
        # Date patterns
        self.date_patterns = [
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{4})\b',
            r'\b(\d{1,2})\/(\d{4})\b',
            r'\b(\d{4})\s*[-–]\s*(\d{4}|Present|Current)\b',
            r'\b(\d{4})\b',
        ]
        
        # Company patterns
        self.company_patterns = [
            r'\b([A-Z][a-zA-Z\s&,.-]*(?:Inc|LLC|Corp|Corporation|Company|Ltd|Limited|Technologies|Tech|Systems|Solutions|Services|Group|Pvt|Private)\.?)\b',
            r'\b([A-Z][a-zA-Z\s&,.-]+)\s+[-–]\s+[A-Z]',
            r'\b([A-Z][a-zA-Z\s&,.-]{2,})\b(?=\s*[\n,])',
        ]
        
        print("Regex patterns loaded successfully!")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading TXT: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text based on file extension"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information using regex patterns"""
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Extract phone
        phone_patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?[0-9]{1,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
            r'\b\d{10}\b'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match)
                    if phone.isdigit() and len(phone) == 10:
                        phones.append(phone)
                else:
                    if match.replace('-', '').replace('.', '').replace(' ', '').isdigit():
                        phones.append(match)
        
        # Extract LinkedIn
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile/view\?id=)([A-Za-z0-9-]+)'
        linkedin_matches = re.findall(linkedin_pattern, text)
        linkedin_url = f"linkedin.com/in/{linkedin_matches[0]}" if linkedin_matches else ""
        
        # Extract name from top of document
        names = self.extract_name_regex(text)
        
        # Extract title
        title = self.extract_title_regex(text)
        
        # Extract location
        location = self.extract_location_regex(text)
        
        return {
            "first_name": names.get('first_name', ''),
            "last_name": names.get('last_name', ''),
            "title": title,
            "mail": emails[0] if emails else "",
            "phone": phones[0] if phones else "",
            "linkedin": linkedin_url,
            "country": location.get('country', ''),
            "state": location.get('state', ''),
            "city": location.get('city', '')
        }
    
    def extract_name_regex(self, text: str) -> Dict[str, str]:
        """Extract name using regex patterns focusing on document structure"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look in first 5 lines for name
        for i, line in enumerate(lines[:5]):
            # Skip lines with email, phone, or common resume keywords
            if any(keyword in line.lower() for keyword in ['email', 'phone', 'linkedin', 'github', 'address', '@']):
                continue
            
            # Skip lines that are too long (likely not just a name)
            if len(line) > 50:
                continue
            
            # Check against name patterns
            for pattern in self.name_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    full_name = match.group(1).strip()
                    name_parts = full_name.split()
                    
                    # Filter out obvious non-names
                    if any(word.lower() in ['resume', 'cv', 'curriculum', 'vitae', 'profile'] for word in name_parts):
                        continue
                    
                    if len(name_parts) >= 2:
                        return {
                            "first_name": name_parts[0],
                            "last_name": ' '.join(name_parts[1:])
                        }
                    elif len(name_parts) == 1 and len(name_parts[0]) > 1:
                        return {
                            "first_name": name_parts[0],
                            "last_name": ""
                        }
        
        return {"first_name": "", "last_name": ""}
    
    def extract_title_regex(self, text: str) -> str:
        """Extract professional title using regex patterns"""
        lines = text.split('\n')[:15]  # Check first 15 lines
        
        for line in lines:
            line = line.strip()
            if len(line) < 5 or len(line) > 100:  # Skip very short or very long lines
                continue
            
            # Check against title patterns
            for pattern in self.title_patterns:
                match = re.search(pattern, line)
                if match:
                    # Clean up the title
                    title = line.strip()
                    # Remove common prefixes/suffixes
                    title = re.sub(r'^\W+|\W+$', '', title)
                    return title
        
        # Fallback: look for lines that might be titles based on position and content
        for i, line in enumerate(lines):
            line = line.strip()
            if i > 0 and i < 10 and 10 < len(line) < 60:
                # If line contains role-related keywords
                if any(keyword in line.lower() for keyword in 
                      ['engineer', 'developer', 'manager', 'analyst', 'consultant', 'specialist', 'lead', 'senior', 'junior']):
                    return line
        
        return ""
    
    def extract_location_regex(self, text: str) -> Dict[str, str]:
        """Extract location using regex patterns"""
        # Look in first 20 lines for location
        lines = text.split('\n')[:20]
        
        for line in lines:
            for pattern in self.location_patterns:
                match = re.search(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) >= 3 and groups[2]:  # City, State, Country
                        return {
                            "city": groups[0].strip(),
                            "state": groups[1].strip(),
                            "country": groups[2].strip()
                        }
                    elif len(groups) >= 2:  # City, State or City, Country
                        return {
                            "city": groups[0].strip(),
                            "state": groups[1].strip(),
                            "country": ""
                        }
        
        return {"city": "", "state": "", "country": ""}
    
    def extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience using improved regex patterns"""
        experience_section = self.extract_section(text, ['experience', 'work', 'employment', 'career', 'professional'])
        experiences = []
        
        if not experience_section:
            return experiences
        
        # Split by date patterns or clear job separators
        entries = re.split(r'\n(?=\d{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', experience_section)
        
        for entry in entries:
            if len(entry.strip()) < 30:  # Skip very short entries
                continue
                
            experience = self.parse_experience_entry(entry)
            if experience['role'] or experience['company']:
                experiences.append(experience)
        
        return experiences
    
    def parse_experience_entry(self, entry: str) -> Dict[str, str]:
        """Parse a single work experience entry with improved regex"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        
        role = ""
        company = ""
        location = ""
        start_date = ""
        end_date = ""
        description = ""
        
        # Extract all dates from entry
        all_dates = []
        for line in lines:
            # Multiple date pattern matching
            for pattern in self.date_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:  # Month Year or MM/YYYY
                            date_str = f"{match[0]} {match[1]}" if match[0].isalpha() else f"{match[0]}/{match[1]}"
                            all_dates.append(date_str)
                        else:
                            all_dates.extend([m for m in match if m])
                    else:
                        all_dates.append(match)
        
        # Clean and assign dates
        unique_dates = list(dict.fromkeys(all_dates))  # Remove duplicates while preserving order
        if len(unique_dates) >= 2:
            start_date = unique_dates[0]
            end_date = unique_dates[1]
        elif len(unique_dates) == 1:
            end_date = unique_dates[0]
            start_date = ""
        
        # Extract role (usually first meaningful line)
        if lines:
            first_line = lines[0]
            # If first line doesn't contain dates or company indicators, it's likely the role
            if not any(re.search(pattern, first_line) for pattern in self.date_patterns):
                role = first_line
        
        # Extract company using patterns
        for line in lines:
            for company_pattern in self.company_patterns:
                match = re.search(company_pattern, line)
                if match:
                    potential_company = match.group(1).strip()
                    # Validate it's not a role or description
                    if len(potential_company) > 3 and potential_company != role:
                        company = potential_company
                        break
            if company:
                break
        
        # If no company found with patterns, look for capitalized entities
        if not company:
            for line in lines[1:3]:  # Check next few lines
                words = line.split()
                if words and len(words) <= 5:  # Company names are usually short
                    if all(word[0].isupper() for word in words if len(word) > 2):
                        company = line
                        break
        
        # Extract description (remaining lines that aren't role, company, or dates)
        description_lines = []
        for line in lines:
            # Skip if line is role, company, or contains only dates
            if (line != role and line != company and 
                not any(date in line for date in unique_dates) and
                len(line) > 10):
                description_lines.append(line)
        
        description = ' '.join(description_lines[:3]).strip()  # Limit description length
        
        return {
            "role": role,
            "company": company,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "work_description": description
        }
    
    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract projects with improved parsing"""
        projects_section = self.extract_section(text, ['projects', 'project work', 'personal projects', 'key projects'])
        projects = []
        
        if not projects_section:
            return projects
        
        # Split by project indicators (bullets, numbers, or clear separators)
        entries = re.split(r'\n(?=•|\d+\.|\*|\-\s*[A-Z]|[A-Z][a-zA-Z\s]+:)', projects_section)
        
        for entry in entries:
            if len(entry.strip()) < 20:
                continue
                
            project = self.parse_project_entry(entry)
            if project['project_name']:
                projects.append(project)
        
        return projects
    
    def parse_project_entry(self, entry: str) -> Dict[str, str]:
        """Parse a single project entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        
        project_name = ""
        company_name = ""
        start_date = ""
        end_date = ""
        description = ""
        
        if lines:
            # Clean project name (remove bullets, numbers)
            first_line = lines[0]
            project_name = re.sub(r'^[•\*\-\d\.\)\s]+', '', first_line).strip()
            # Remove trailing colons
            project_name = re.sub(r':$', '', project_name).strip()
        
        # Extract dates
        all_dates = []
        for line in lines:
            for pattern in self.date_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    if isinstance(match, tuple):
                        all_dates.extend([m for m in match if m and m != 'Present'])
                    else:
                        all_dates.append(match)
        
        if len(all_dates) >= 2:
            start_date = all_dates[0]
            end_date = all_dates[1]
        elif len(all_dates) == 1:
            start_date = all_dates[0]
        
        # Description is usually the remaining content
        description_lines = []
        for line in lines[1:]:
            if not any(date in line for date in all_dates):
                description_lines.append(line)
        
        description = ' '.join(description_lines).strip()
        
        return {
            "project_name": project_name,
            "company_name": company_name,
            "start_date": start_date,
            "end_date": end_date,
            "project_description": description
        }
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information with better regex patterns"""
        education_section = self.extract_section(text, ['education', 'academic', 'qualification', 'academic background'])
        education_list = []
        
        if not education_section:
            return education_list
        
        # Split by dates or clear education separators
        entries = re.split(r'\n(?=\d{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', education_section)
        
        for entry in entries:
            if len(entry.strip()) < 15:
                continue
                
            education = self.parse_education_entry(entry)
            if education['institution'] or education['degree']:
                education_list.append(education)
        
        return education_list
    
    def parse_education_entry(self, entry: str) -> Dict[str, str]:
        """Parse a single education entry with improved patterns"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        
        institution = ""
        address = ""
        degree = ""
        field = ""
        start_date = ""
        end_date = ""
        
        # Extract dates
        all_dates = []
        for line in lines:
            for pattern in self.date_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    if isinstance(match, tuple):
                        all_dates.extend([m for m in match if m])
                    else:
                        all_dates.append(match)
        
        if len(all_dates) >= 2:
            start_date = all_dates[0]
            end_date = all_dates[1]
        elif len(all_dates) == 1:
            end_date = all_dates[0]  # Usually graduation date
        
        # Enhanced degree patterns
        degree_patterns = [
            r'\b(Bachelor\s+of\s+\w+|Master\s+of\s+\w+|Doctor\s+of\s+\w+)',
            r'\b(B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?|M\.?B\.?A\.?)',
            r'\b(B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?)',
            r'\b(Diploma|Certificate|Associate)',
            r'\b(Bachelor|Master|Doctorate)(?:\s+in\s+[\w\s]+)?'
        ]
        
        for line in lines:
            for pattern in degree_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Get the full line as degree info
                    degree = line.strip()
                    # Extract field if "in" is present
                    field_match = re.search(r'\bin\s+([\w\s]+?)(?:\s|$|,)', line, re.IGNORECASE)
                    if field_match:
                        field = field_match.group(1).strip()
                    break
            if degree:
                break
        
        # Enhanced institution patterns
        institution_keywords = ['university', 'college', 'institute', 'school', 'academy']
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in institution_keywords):
                # Clean up the institution name
                institution = re.sub(r'\b\d{4}\b', '', line).strip()  # Remove years
                institution = re.sub(r'\s+', ' ', institution).strip()  # Clean spaces
                break
        
        # If no clear institution found, use heuristics
        if not institution:
            for line in lines:
                # Look for lines that are likely institution names
                if (len(line) > 5 and len(line) < 100 and 
                    not any(date in line for date in all_dates) and
                    line != degree):
                    institution = line
                    break
        
        return {
            "institution": institution,
            "address": address,
            "degree": degree,
            "field": field,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extract languages with comprehensive patterns"""
        languages_section = self.extract_section(text, ['languages', 'language skills', 'spoken languages'])
        languages = []
        
        if not languages_section:
            return languages
        
        # Comprehensive language list
        language_list = [
            'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Russian', 
            'Chinese', 'Mandarin', 'Cantonese', 'Japanese', 'Korean', 'Arabic', 'Hindi', 
            'Bengali', 'Tamil', 'Telugu', 'Marathi', 'Gujarati', 'Punjabi', 'Urdu', 
            'Thai', 'Vietnamese', 'Dutch', 'Swedish', 'Norwegian', 'Danish', 'Finnish',
            'Polish', 'Czech', 'Hungarian', 'Romanian', 'Bulgarian', 'Greek', 'Hebrew',
            'Turkish', 'Indonesian', 'Malay', 'Filipino', 'Tagalog'
        ]
        
        proficiency_levels = [
            'Native', 'Fluent', 'Professional', 'Conversational', 'Basic', 'Beginner', 
            'Intermediate', 'Advanced', 'Bilingual', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2',
            'Elementary', 'Limited', 'Working'
        ]
        
        lines = languages_section.split('\n')
        for line in lines:
            for language in language_list:
                if re.search(r'\b' + re.escape(language) + r'\b', line, re.IGNORECASE):
                    proficiency = ""
                    
                    # Look for proficiency in the same line
                    for level in proficiency_levels:
                        if re.search(r'\b' + re.escape(level) + r'\b', line, re.IGNORECASE):
                            proficiency = level
                            break
                    
                    # Avoid duplicates
                    if not any(lang['language'].lower() == language.lower() for lang in languages):
                        languages.append({
                            "language": language,
                            "proficiency": proficiency
                        })
        
        return languages
    
    def extract_certifications(self, text: str) -> List[Dict[str, str]]:
        """Extract certifications with better parsing"""
        cert_section = self.extract_section(text, ['certifications', 'certificates', 'licenses', 'credentials'])
        certifications = []
        
        if not cert_section:
            return certifications
        
        lines = cert_section.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) < 5:
                continue
            
            # Clean the line (remove bullets, etc.)
            cleaned_line = re.sub(r'^[•\*\-\d\.\)\s]+', '', line).strip()
            
            # Extract dates
            all_dates = []
            for pattern in self.date_patterns:
                matches = re.findall(pattern, cleaned_line)
                for match in matches:
                    if isinstance(match, tuple):
                        all_dates.extend([m for m in match if m])
                    else:
                        all_dates.append(match)
            
            start_date = ""
            end_date = ""
            if len(all_dates) >= 2:
                start_date = all_dates[0]
                end_date = all_dates[1]
            elif len(all_dates) == 1:
                start_date = all_dates[0]
            
            # Remove dates to get cert name
            cert_name = cleaned_line
            for date in all_dates:
                cert_name = cert_name.replace(date, '')
            cert_name = re.sub(r'\s+', ' ', cert_name).strip()
            cert_name = re.sub(r'^[-,\s]+|[-,\s]+$', '', cert_name)
            
            # Extract platform
            platform = ""
            platforms = [
                'Coursera', 'edX', 'Udemy', 'LinkedIn Learning', 'Pluralsight',
                'AWS', 'Microsoft', 'Google', 'Cisco', 'Oracle', 'IBM',
                'Salesforce', 'Adobe', 'Autodesk', 'VMware'
            ]
            
            for p in platforms:
                if re.search(r'\b' + re.escape(p) + r'\b', cert_name, re.IGNORECASE):
                    platform = p
                    break
            
            if cert_name and len(cert_name) > 3:
                certifications.append({
                    "name": cert_name,
                    "platform": platform,
                    "start_date": start_date,
                    "end_date": end_date
                })
        
        return certifications
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills with comprehensive patterns"""
        skills_section = self.extract_section(text, ['skills', 'technical skills', 'technologies', 'competencies'])
        
        if not skills_section:
            skills_section = text  # Fallback to entire text
        
        # Comprehensive skill database
        skill_categories = {
            'programming': [
                'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust', 
                'Swift', 'Kotlin', 'TypeScript', 'Scala', 'R', 'MATLAB', 'Perl', 'Shell', 
                'Bash', 'PowerShell', 'VB.NET', 'Objective-C', 'Dart', 'Elixir', 'Haskell'
            ],
            'web': [
                'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Django', 
                'Flask', 'Spring', 'Laravel', 'ASP.NET', 'jQuery', 'Bootstrap', 'Sass', 
                'Less', 'Webpack', 'Next.js', 'Nuxt.js', 'Gatsby', 'Svelte'
            ],
            'database': [
                'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 
                'Cassandra', 'DynamoDB', 'Neo4j', 'Elasticsearch', 'MariaDB', 'CouchDB'
            ],
            'cloud': [
                'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub', 
                'GitLab', 'Terraform', 'Ansible', 'CI/CD', 'Linux', 'Unix', 'DevOps'
            ],
            'data_science': [
                'Machine Learning', 'Deep Learning', 'Data Science', 'Artificial Intelligence',
                'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy', 'Matplotlib', 
                'Seaborn', 'Jupyter', 'Tableau', 'Power BI', 'Apache Spark', 'Hadoop'
            ],
            'soft_skills': [
                'Leadership', 'Communication', 'Problem Solving', 'Team Work', 
                'Project Management', 'Agile', 'Scrum', 'Kanban'
            ]
        }
        
        all_skills = []
        for category_skills in skill_categories.values():
            all_skills.extend(category_skills)
        
        skills_text = skills_section.lower()
        found_skills = []
        
        for skill in all_skills:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, skills_text):
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_designations(self, text: str) -> List[str]:
        """Extract professional designations with comprehensive patterns"""
        designation_patterns = [
            # Professional certifications
            r'\b(CPA|PMP|CISSP|CISA|CISM|CRISC|FRM|CFA|CMA|CIA|ACCA|CA|CS|CWA)\b',
            # Academic degrees
            r'\b(PE|PEng|PhD|MD|JD|MBA|MS|BS|BA|MA|DDS|PharmD|DO)\b',
            # IT certifications
            r'\b(CCNA|CCNP|CCIE|MCSE|MCSA|CEH|OSCP|CISSP|CISM|GSEC)\b',
            # Cloud certifications
            r'\b(AWS|Azure|GCP|Solutions Architect|Cloud Practitioner)\b',
            # Other professional designations
            r'\b(PgMP|PSM|CSM|CSPO|SAFe|ITIL|Six Sigma|Lean)\b'
        ]
        
        designations = []
        for pattern in designation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            designations.extend([match.upper() for match in matches])
        
        return list(set(designations))  # Remove duplicates
    
    def extract_section(self, text: str, keywords: List[str]) -> str:
        """Extract a specific section from the text based on keywords"""
        lines = text.split('\n')
        section_start = -1
        section_end = len(lines)
        
        # Find section start
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            # Check if line contains any of the keywords
            if any(keyword in line_lower for keyword in keywords):
                # Additional validation: line should be relatively short (likely a header)
                if len(line.strip()) < 50:
                    section_start = i
                    break
        
        if section_start == -1:
            return ""
        
        # Find section end (next major section)
        major_sections = [
            'education', 'experience', 'skills', 'projects', 'certifications',
            'languages', 'awards', 'publications', 'references', 'summary',
            'objective', 'profile', 'achievements', 'hobbies', 'interests'
        ]
        
        for i in range(section_start + 1, len(lines)):
            line_lower = lines[i].lower().strip()
            if len(line_lower) > 0 and len(line_lower) < 50:  # Potential section header
                if any(section in line_lower for section in major_sections):
                    # Make sure it's not part of current section
                    if not any(keyword in line_lower for keyword in keywords):
                        section_end = i
                        break
        
        return '\n'.join(lines[section_start:section_end])
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere with parsing
        text = re.sub(r'[^\w\s@.,;:\-\(\)\/]', ' ', text)
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.match(email_pattern, email) is not None
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Check if it's a valid length (10-15 digits)
        return 10 <= len(digits_only) <= 15
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Main function to parse resume and return structured JSON"""
        
        try:
            # Extract text from file
            text = self.extract_text(file_path)
            
            if not text:
                return {"error": "Could not extract text from file"}
            
            # Clean the text
            text = self.clean_text(text)
            
            # Extract all components
            personal_info = self.extract_personal_info(text)
            work_experience = self.extract_work_experience(text)
            projects = self.extract_projects(text)
            education = self.extract_education(text)
            languages = self.extract_languages(text)
            certifications = self.extract_certifications(text)
            skills = self.extract_skills(text)
            designations = self.extract_designations(text)
            
            # Validate extracted data
            if personal_info['mail'] and not self.validate_email(personal_info['mail']):
                personal_info['mail'] = ""
            
            if personal_info['phone'] and not self.validate_phone(personal_info['phone']):
                personal_info['phone'] = ""
            
            # Structure the output
            parsed_resume = {
                "personal_info": personal_info,
                "work_experience": work_experience,
                "projects": projects,
                "education": education,
                "languages": languages,
                "certifications": certifications,
                "skills": skills,
                "designations": designations
            }
            
            return parsed_resume
            
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            return {"error": f"Error parsing resume: {str(e)}"}


# def main():
#     """Example usage with error handling"""
#     parser = ResumeExtracter()
    
#     # Example file path - replace with your resume file
#     file_path = r""  # Change this to your resume file path
    
#     try:
#         result = parser.parse_resume(file_path)
        
#         if "error" in result:
#             print(f"Error: {result['error']}")
#             return
        
#         print(json.dumps(result, indent=2, ensure_ascii=False))
        
#     except FileNotFoundError:
#         print(f"Error: File '{file_path}' not found.")
#         print("Please make sure the file exists and the path is correct.")
#     except Exception as e:
#         print(f"Unexpected error: {e}")


# if __name__ == "__main__":
#     main()