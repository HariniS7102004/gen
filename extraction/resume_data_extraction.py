import re
import json
import PyPDF2
import docx
from datetime import datetime
import spacy
import phonenumbers
from rapidfuzz import process, fuzz
from email_validator import validate_email, EmailNotValidError
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeExtractor:
    def __init__(self):
        # Load spaCy model (install with: python -m spacy download en_core_web_sm)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Please install spaCy English model: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Compile regex patterns
        self._compile_patterns()
        
        # Skills database
        self.job_specific_skills = [
            'angular', 'asana', 'aws', 'c programming', 'c#', 'c++', 'cassandara', 'confluence', 'clickup',
            'css', 'django', 'docker', 'express', 'figma', 'flask', 'git', 'go',
            'gcp', 'html', 'java', 'javascript', 'jenkins', 'jira', 'kotlin',
            'kubernetes', 'mongodb', 'mysql', 'node.js', 'numpy', 'oracle',
            'pandas', 'php', 'photoshop', 'postgresql', 'power bi', 'pytorch',
            'python', 'react', 'redis', 'ruby', 'rust', 'scikit-learn', 'slack',
            'spring', 'sql', 'sqlite', 'tableau', 'terraform', 'tensorflow',
            'trello', 'vue'
        ]
        
        self.general_skills = [
            'Accessibility awareness', 'Accountability', 'Active listening', 'Adaptability', 'Analytical skills',
            'Attention to detail', 'Brand representation', 'Budget management', 'Change management', 'Client relations',
            'Collaboration', 'Community engagement', 'Compliance awareness', 'Conflict management', 'Conflict resolution',
            'Contingency planning', 'Continuous learning', 'Contract review', 'Creativity', 'Crisis management',
            'Cross-functional collaboration', 'Cultural awareness', 'Customer service', 'Data collection', 'Data interpretation',
            'Deadline management', 'Decision-making', 'Delegation', 'Diversity inclusion', 'Effective communication',
            'Emotional intelligence', 'Environmental consideration', 'Ethical judgment', 'Feedback acceptance', 'Feedback delivery',
            'Forecasting', 'Goal alignment', 'Goal setting', 'Health advocacy', 'Innovation', 'Initiative',
            'Integrity', 'Interpersonal skills', 'Knowledge sharing', 'Leadership', 'Market awareness',
            'Meeting facilitation', 'Mentoring', 'Multitasking', 'Negotiation', 'Organization',
            'Peer support', 'Performance evaluation', 'Performance tracking', 'Persuasion', 'Policy adherence',
            'Presentation skills', 'Prioritization', 'Problem identification', 'Problem-solving', 'Process documentation',
            'Process improvement', 'Product knowledge', 'Project management', 'Proactivity', 'Public speaking',
            'Quality assurance', 'Report writing', 'Research', 'Resource allocation', 'Resource management',
            'Resilience', 'Risk assessment', 'Risk mitigation', 'Safety compliance', 'Self-assessment',
            'Self-motivation', 'Service delivery', 'Stakeholder engagement', 'Strategic planning', 'Strategic thinking',
            'Stress management', 'Task coordination', 'Team building', 'Team motivation', 'Teamwork',
            'Time allocation', 'Time management', 'Training facilitation', 'Transparency', 'Trend analysis',
            'Verbal communication', 'Vendor management', 'Wellness promotion', 'Workflow optimization', 'Written communication'
        ]

        
        # Proficiency levels
        self.proficiency_levels = [
            'advanced', 'basic', 'bilingual', 'beginner', 'conversational', 'elementary', 'Elementary Proficiency', 'fluent', 'Full Professional Proficiency',
            'intermediate', 'Limited Working Proficiency', 'native', 'native bilingual proficiency', 'professional working proficiency', 'Reading Only',
            'Upper Intermediate'
        ]
        
        # Common job titles and education degrees
        self.job_titles = [
            'AI Ethics Specialist', 'AI Research Scientist', 'AI/ML Engineer', 'Agile Project Manager', 'analyst', 'Automotive Engineer', 'Backend Developer',
            'Big Data Engineer', 'Blockchain Developer', 'Brand Manager', 'Building Operations Manager', 'Business Analyst', 'Business Development Manager',
            'Change Manager', 'Client Relations Manager', 'Cloud Engineer', 'Community Manager', 'Compensation and Benefits Manager', 'Compliance Manager',
            'Computer Vision Engineer', 'consultant', 'Control Systems Engineer', 'coordinator', 'Corporate Strategy Manager', 'Crisis Manager',
            'Cryptography Specialist', 'Customer Service Manager', 'Customer Success Manager', 'Cybersecurity Specialist', 'Data Analyst', 'Data Architect',
            'Data Engineer', 'Data Scientist', 'designer', 'developer', 'Developer', 'DevOps Engineer', 'Digital Marketing Manager', 'Digital Product Manager',
            'director', 'Electrical Engineer', 'Electronics Engineer', 'Embedded Software Developer', 'Embedded Systems Engineer', 'Employee Engagement Manager',
            'Employee Relations Manager', 'engineer', 'Event Manager', 'E-commerce Product Manager', 'Facility Manager', 'Facility Operations Manager',
            'Financial Analyst', 'Financial Manager', 'Fleet Manager', 'Frontend Developer', 'Full Stack Developer', 'Game Developer', 'Green Energy Engineer',
            'Healthcare IT Specialist', 'HR Manager', 'Information Security Manager', 'Innovation Manager', 'intern ', 'Inventory Manager', 'IT Business Analyst',
            'IT Manager', 'IT Project Manager', 'IT Security Specialist', 'IT Systems Engineer', 'Java Developer', 'junior', 'Key Account Manager',
            'lead', 'Leadership Development Manager', 'Logistics Manager', 'Maintenance Manager', 'manager', 'Manufacturing Operations Manager',
            'Market Research Analyst', 'Marketing Manager', 'Mergers and Acquisitions Manager', 'Machine Learning Engineer', 'Mobile App Developer',
            'Natural Language Processing Engineer', 'Network Engineer', 'Network Manager', 'Network Security Engineer', 'Operations Manager', 
            'Operations Research Analyst', 'Organizational Development Manager', 'Penetration Tester', 'Policy Analyst', 'Process Improvement Manager',
            'Procurement Manager', 'Product Manager', 'Program Manager', 'Project Manager', 'Psychology Researcher', 'Purchasing Manager', 'Python Developer',
            'Quality Assurance Manager', 'Regional Sales Manager', 'Research Scientist', 'researcher', 'Risk Manager', 'Sales Manager', 'scientist',
            'Security Analyst', 'Security Manager', 'senior', 'Social Media Manager', 'Software Developer', 'Software Engineer', 'specialist',
            'Sports Team Manager', 'Strategic Planning Manager', 'Strategic Researcher', 'Strategic Risk Consultant', 'Strategic Solutions Architect',
            'Strategic Workforce Analyst', 'Strategist', 'Strategist Consultant', 'Strategist Researcher', 'Strategist Specialist', 'Strategist Support Analyst',
            'Strategist Technologist', 'Strategist UX Designer', 'Strategist-Developer', 'Strategist-Engineer', 'Strategist-Marketer', 'Strategist-Planner',
            'Strategist-Product Manager', 'Strategist-Researcher', 'Strategist-Writer', 'Strategist–Designer', 'Strategist–Technologist', 'Strategist–Visionary',
            'Strategist–Writer', 'Strategist/Creative Lead', 'Strategy Analyst', 'Strategy Consultant', 'Strategy Coordinator', 'Strategy Director',
            'Strategy Lead', 'Strategy Manager', 'Strategy Planner', 'Strategy Researcher', 'Strategy Specialist', 'Strategy Support Analyst',
            'Strategy Technologist', 'Strategy UX Designer', 'Strategy-Developer', 'Strategy-Engineer', 'Strategy-Marketer', 'Strategy-Planner',
            'Strategy-Product Manager', 'Strategy-Researcher', 'Strategy-Writer', 'Strategy–Designer', 'Strategy–Technologist', 'Strategy–Visionary',
            'Strategy–Writer', 'Strategy/Creative Lead', 'Strategyst', 'Strategyst Analyst', 'Strategyst Consultant', 'Strategyst Coordinator',
            'Strategyst Director', 'Strategyst Lead', 'Strategyst Manager', 'Strategyst Planner', 'Strategyst Researcher', 'Strategyst Specialist',
            'Strategyst Support Analyst', 'Strategyst Technologist', 'Strategyst UX Designer', 'Strategyst-Developer', 'Strategyst-Engineer',
            'Strategyst-Marketer', 'Strategyst-Planner', 'Strategyst-Product Manager', 'Strategyst-Researcher', 'Strategyst-Writer', 'Strategyst–Designer',
            'Strategyst–Technologist', 'Strategyst–Visionary', 'Strategyst–Writer', 'Strategyst/Creative Lead', 'Strategystic Analyst', 'Strategystic Consultant',
            'Strategystic Coordinator', 'Strategystic Director', 'Strategystic Lead', 'Strategystic Manager', 'Strategystic Planner', 'Strategystic Researcher',
            'Strategystic Specialist', 'Strategystic Support Analyst', 'Strategystic Technologist', 'Strategystic UX Designer', 'Strategystic-Developer',
            'Strategystic-Engineer', 'Strategystic-Marketer', 'Strategystic-Planner', 'Strategystic-Product Manager', 'Strategystic-Researcher',
            'Strategystic-Writer', 'Strategystic–Designer', 'Strategystic–Technologist', 'Strategystic–Visionary', 'Strategystic–Writer', 'Strategystic/Creative Lead',
            'Supply Chain Analyst', 'Supply Chain Manager', 'supervisor', 'Systems Analyst', 'Systems Engineer', 'Systems Manager', 'Technical Support Manager',
            'Telecommunications Engineer', 'Test Manager', 'Testing Engineer', 'Training and Development Manager', 'Transition Manager', 'Venue Manager'
        ]
        
        self.degree_types = [
            'Bachelor of Architecture', 'Bachelor of Arts', 'Bachelor of Business Administration',
            'Bachelor of Commerce', 'Bachelor of Computer Applications', 'Bachelor of Computer Science Engineering',
            'Bachelor of Design', 'Bachelor of Education', 'Bachelor of Engineering', 'Bachelor of Fine Arts',
            'Bachelor of Law', 'Bachelor of Pharmacy', 'Bachelor of Philosophy', 'Bachelor of Science',
            'Bachelor of Social Work', 'b.e', 'b.sc', 'b.tech', 'bachelor', 'bca', 'diploma',
            'Diploma in Accounting', 'Diploma in Business Management', 'Diploma in Civil Engineering',
            'Diploma in Computer Science', 'Diploma in Education', 'Diploma in Electrical Engineering',
            'Diploma in Hotel Management', 'Diploma in Marketing', 'Diploma in Mechanical Engineering',
            'Doctor of Education', 'Doctor of Medicine', 'Doctor of Philosophy', 'doctorate', 'High School',
            'Higher Secondary', 'm.e', 'm.sc', 'm.tech', 'master', 'Master of Architecture', 'Master of Arts',
            'Master of Business Administration', 'Master of Commerce', 'Master of Computer Applications',
            'Master of Computer Science Engineering', 'Master of Design', 'Master of Education',
            'Master of Engineering', 'Master of Fine Arts', 'Master of Law', 'Master of Philosophy',
            'Master of Pharmacy', 'Master of Science', 'Master of Social Work', 'mba', 'mca', 'phd',
            'Secondary School'
        ]


        self.certifications = [
            'AWS Certified Developer',
            'AWS Certified Solutions Architect',
            'Azure Developer Associate',
            'Certified Agile Developer',
            'Certified Associate in Project Management (CAPM)',
            'Certified Business Analysis Professional (CBAP)',
            'Certified Data Scientist',
            'Certified Energy Manager',
            'Certified Ethical Hacker (CEH)',
            'Certified in Logistics, Transportation and Distribution (CLTD)',
            'Certified in Production and Inventory Management (CPIM)',
            'Certified Information Systems Security Professional (CISSP)',
            'Certified Kubernetes Administrator (CKA)',
            'Certified Management Accountant (CMA)',
            'Certified Manufacturing Engineer',
            'Certified Public Accountant (CPA)',
            'Certified Quality Engineer',
            'Certified Scrum Master (CSM)',
            'Certified Supply Chain Professional (CSCP)',
            'Certified Systems Engineering Professional',
            'Certified Welding Engineer',
            'Chartered Financial Analyst (CFA)',
            'Cisco Certified Internetwork Expert (CCIE)',
            'Cisco Certified Network Associate (CCNA)',
            'Cisco Certified Network Professional (CCNP)',
            'CompTIA Security+',
            'Engineer in Training Certificate',
            'Engineering Management Certification Fundamentals',
            'Google Analytics Certification',
            'Google Associate Cloud Engineer',
            'Google Cloud Certified Professional Cloud Architect',
            'HubSpot Inbound Certification',
            'IIBA Agile Analysis Certification (IIBA-AAC)',
            'ITIL Foundation Certification',
            'ML Certified Developer',
            'Oracle Certified Java Programmer',
            'Power BI Data Analyst Associate',
            'Professional Design Engineer (PDE) License',
            'Project Management Professional (PMP)',
            'Project Management Tech (PMT)',
            'Structural Engineer (SE)',
            'TensorFlow Developer Certificate'
        ]

        self.platforms = [
            'AWS', 'Coursera', 'Cisco', 'edX', 'Google', 'Great Learning', 'HubSpot', 'IBM',
            'Khan Academy', 'LinkedIn', 'Meta', 'Microsoft', 'NPTEL', 'Oracle', 'Pluralsight',
            'Salesforce', 'Simplilearn', 'Udacity', 'Udemy', 'Wharton', 'HarvardX', 'MITx',
            'OpenLearn', 'Oracle', 'FutureLearn', 'DataCamp', 'Skillshare', 'Alison', 'Codecademy',
            'Scrum Alliance', 'Project Management Institute', 'CompTIA', 'ISACA'
        ]


        self.languages = [
            'Arabic', 'Bengali', 'Chinese', 'Czech', 'Danish', 'Dutch', 'English', 'Finnish', 'French', 'German',
            'Greek', 'Hebrew', 'Hindi', 'Hungarian', 'Indonesian', 'Italian', 'Japanese', 'Korean', 'Malay', 'Mandarin',
            'Norwegian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Spanish', 'Swahili', 'Swedish', 'Tamil', 'Thai',
            'Turkish', 'Ukrainian', 'Vietnamese'
        ]



    def _compile_patterns(self):
        """Compile all regex patterns for better performance"""
        # Email pattern
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Phone patterns (various formats)
        self.phone_patterns = [
            re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'(\+\d{1,3}[-.\s]?)?\d{10}'),
            re.compile(r'(\+\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}')
        ]
        
        # URL pattern
        self.url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
        
        # LinkedIn pattern
        self.linkedin_pattern = re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?', re.IGNORECASE)
        
        # GitHub pattern
        self.github_pattern = re.compile(r'(?:https?://)?(?:www\.)?github\.com/[\w-]+/?', re.IGNORECASE)
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'),  # MM/DD/YYYY or DD/MM/YYYY
            re.compile(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'),  # YYYY/MM/DD
            re.compile(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[,\s]+(\d{4})', re.IGNORECASE),
            re.compile(r'(\d{4})[,\s]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', re.IGNORECASE),
            re.compile(r'(\d{1,2})[,\s]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[,\s]+(\d{4})', re.IGNORECASE)
        ]
        
        # Section headers
        self.section_patterns = {
            'experience': re.compile(r'\b(?:work\s+)?(?:professional\s+)?experience\b|employment\s+history|work\s+history', re.IGNORECASE),
            'education': re.compile(r'\beducation\b|academic\s+background|qualifications', re.IGNORECASE),
            'skills': re.compile(r'\bskills\b|technical\s+skills|competencies|expertise', re.IGNORECASE),
            'projects': re.compile(r'\bprojects?\b|portfolio', re.IGNORECASE),
            'certifications': re.compile(r'\bcertifications?\b|licenses?|credentials', re.IGNORECASE),
            'languages': re.compile(r'\blanguages?\b|linguistic\s+skills', re.IGNORECASE),
            'achievements': re.compile(r'\bachievements?\b|awards|honors|recognitions?', re.IGNORECASE),
            'links': re.compile(r'\blinks\b|online\s+profiles|social\s+profiles|websites?', re.IGNORECASE),
            'address': re.compile(r'\baddress\b|location|residence|contact\s+information', re.IGNORECASE),
            'summary': re.compile(r'\b(summary|profile|professional\s+summary|about\s+me)\b', re.IGNORECASE),
            'interests': re.compile(r'\binterests\b|hobbies|activities', re.IGNORECASE),
            'publications': re.compile(r'\bpublications?\b|articles|papers', re.IGNORECASE),
            'references': re.compile(r'\breferences?\b|referees', re.IGNORECASE)
        }

    def extract_text_from_file(self, file_path):
        """Extract text from PDF or DOCX file"""
        text = ""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text()
            
            elif file_extension == '.docx':
                doc = docx.Document(file_path)
                for paragraph in doc.paragraphs:
                    text += paragraph.text + '\n'
            
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            print(f"Error reading file: {e}")
            
        return text.strip()

    def extract_personal_info(self, text):
        """Extract personal information"""
        info = {
            'first_name': '',
            'second_name': '',
            'email': '',
            'phone': '',
            'linkedin_profile': '',
            'country': '',
            'state': '',
            'city': ''
        }
        
        # Extract email
        email_match = self.email_pattern.search(text)
        if email_match:
            try:
                validated_email = validate_email(email_match.group())
                info['email'] = validated_email.email
            except EmailNotValidError:
                pass
        
        # Extract phone
        for pattern in self.phone_patterns:
            phone_match = pattern.search(text)
            if phone_match:
                try:
                    parsed_number = phonenumbers.parse(phone_match.group(), None)
                    if phonenumbers.is_valid_number(parsed_number):
                        info['phone'] = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                        break
                except:
                    info['phone'] = phone_match.group().strip()
                    break
        
        # Extract LinkedIn
        linkedin_match = self.linkedin_pattern.search(text)
        if linkedin_match:
            info['linkedin_profile'] = linkedin_match.group()
        
        # Extract name using spaCy NER
        if self.nlp:
            doc = self.nlp(text[:100])  # Check first 1000 chars for name
            names = []
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(ent.text.split()) <= 3:
                    names.append(ent.text)
            
            if names:
                full_name = names[0].split()
                if len(full_name) >= 1:
                    info['first_name'] = full_name[0]
                if len(full_name) >= 2:
                    info['second_name'] = ' '.join(full_name[1:])
        
        # Extract location
        if self.nlp:
            doc = self.nlp(text)
            locations = []
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:
                    locations.append(ent.text)
            
            if locations:
                # Simple heuristic: assume last location mentioned is current
                location = locations[-1]
                location_parts = location.split(',')
                if len(location_parts) >= 3:
                    info['city'] = location_parts[0].strip()
                    info['state'] = location_parts[1].strip()
                    info['country'] = location_parts[2].strip()
                elif len(location_parts) == 2:
                    info['city'] = location_parts[0].strip()
                    info['state'] = location_parts[1].strip()
                else:
                    info['city'] = location
        
        return info

    def extract_links(self, text):
        """Extract various types of links"""
        links = []
        
        # LinkedIn
        linkedin_matches = self.linkedin_pattern.findall(text)
        for match in linkedin_matches:
            links.append({'type': 'linkedin', 'url': match})
        
        # GitHub
        github_matches = self.github_pattern.findall(text)
        for match in github_matches:
            if {'type': 'github', 'url': match} not in links:
                links.append({'type': 'github', 'url': match})
        
        # Other URLs
        url_matches = self.url_pattern.findall(text)
        for url in url_matches:
            if 'linkedin.com' not in url and 'github.com' not in url:
                if any(blog_word in url.lower() for blog_word in ['blog', 'medium', 'wordpress']):
                    links.append({'type': 'blog', 'url': url})
                elif any(social in url.lower() for social in ['twitter', 'facebook', 'instagram']):
                    links.append({'type': 'social media', 'url': url})
                else:
                    links.append({'type': 'website', 'url': url})
        
        return links

    def parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return ''
        
        date_str = date_str.strip().lower()
        
        # Handle "present", "current", etc.
        if any(word in date_str for word in ['present', 'current', 'now', 'ongoing']):
            return datetime.now().strftime('%Y-%m-%d')
        
        # Try different date patterns
        for pattern in self.date_patterns:
            match = pattern.search(date_str)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 2 and groups[0].isdigit():  # Month Year format
                        year = int(groups[1]) if groups[1].isdigit() else int(groups[0])
                        month_name = groups[0] if not groups[0].isdigit() else groups[1]
                        month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                   'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                        month = month_map.get(month_name[:3], 1)
                        return f"{year}-{month:02d}-01"
                    elif len(groups) == 3:
                        if groups[0].isdigit() and int(groups[0]) > 31:  # YYYY-MM-DD
                            return f"{groups[0]}-{int(groups[1]):02d}-{int(groups[2]):02d}"
                        else:  # MM-DD-YYYY or DD-MM-YYYY
                            return f"{groups[2]}-{int(groups[0]):02d}-{int(groups[1]):02d}"
                except:
                    continue
        
        return date_str

    def extract_work_experience(self, text):
        """Extract work experience"""
        experiences = []
        lines = text.split('\n')
        in_experience_section = False
        experience_lines = []

        # Find experience section
        for line in lines:
            if self.section_patterns['experience'].search(line):
                in_experience_section = True
                continue
            elif in_experience_section and any(
                self.section_patterns[section].search(line)
                for section in self.section_patterns if section != 'experience'
            ):
                if len(experience_lines) < 3:
                    experience_lines = []
                    continue
                else:
                    break
            elif in_experience_section:
                experience_lines.append(line.strip())

        # Parse experience entries
        current_experience = {}
        responsibilities = []
        i = 0

        while i < len(experience_lines):
            line = experience_lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if this line could be a job title/company line
            if self.is_potential_job_line(line):
                # Save previous experience if valid
                if self.is_valid_experience(current_experience):
                    if responsibilities:
                        current_experience['key_responsibilities'] = '\n'.join(responsibilities)
                    experiences.append(current_experience)
                
                # Try to parse new job entry
                parsed_job = self.parse_job_line(line)
                
                # Skip if we couldn't extract both job title and company
                if not parsed_job['job_title'] or not parsed_job['company_name']:
                    i += 1
                    continue
                
                # Initialize new experience
                current_experience = {
                    'job_title': parsed_job['job_title'],
                    'company_name': parsed_job['company_name'],
                    'location': parsed_job['location'],
                    'start_date': parsed_job['start_date'],
                    'enddate': parsed_job['enddate'],
                    'currentwork': parsed_job['currentwork'],
                    'key_responsibilities': ''
                }
                responsibilities = []
                
                # Look for responsibilities in subsequent lines
                j = i + 1
                while j < len(experience_lines):
                    next_line = experience_lines[j].strip()
                    
                    # Stop if empty line or next job entry
                    if not next_line:
                        break
                    
                    if self.is_potential_job_line(next_line):
                        break
                    
                    # Add to responsibilities if not a date line
                    if not self.looks_like_date_line(next_line.lower()):
                        responsibilities.append(next_line)
                    
                    j += 1
                
                # Skip processed lines
                i = j - 1
            
            i += 1

        # Add final experience if valid
        if self.is_valid_experience(current_experience):
            if responsibilities:
                current_experience['key_responsibilities'] = '\n'.join(responsibilities)
            experiences.append(current_experience)

        # Remove duplicates based on job_title and company_name combination
        unique_experiences = []
        seen_combinations = set()

        for exp in experiences:
            # Create a unique identifier based on job title and company
            identifier = (exp['job_title'].lower().strip(), exp['company_name'].lower().strip())
            
            if identifier not in seen_combinations:
                seen_combinations.add(identifier)
                unique_experiences.append(exp)

        return unique_experiences

    def is_potential_job_line(self, line):
        """Check if line could contain job title and company information"""
        # Skip if it's clearly a date line
        if self.looks_like_date_line(line.lower()):
            return False
        
        # Skip if it's just a date or month
        if self.is_just_date_or_month(line):
            return False
        
        # Check for job title indicators
        has_job_title = any(title.lower() in line.lower() for title in self.job_titles)
        
        # Check for separators that typically separate job title from company
        has_separators = any(sep in line for sep in ['@', '|', '–', '-', ',', ' at ', ' with ', ' for '])
        
        # Check for organization patterns
        has_org_pattern = self.has_organization_pattern(line)
        
        # Line should have job title indicators OR separators OR organization patterns
        return has_job_title or has_separators or has_org_pattern

    def is_just_date_or_month(self, line):
        """Check if line contains only dates or months"""
        import re
        
        # Clean the line
        cleaned = re.sub(r'[^\w\s]', ' ', line.lower()).strip()
        words = cleaned.split()
        
        if not words:
            return False
        
        # List of month names and date-related words
        date_words = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
            'present', 'current', 'ongoing', 'to', 'till', 'until'
        ]
        
        # Check if all words are either dates, numbers, or date-related
        for word in words:
            if word.isdigit():
                continue
            if word in date_words:
                continue
            if re.match(r'^\d{4}$', word):  # Year
                continue
            if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', word):  # Date format
                continue
            return False
        
        return True

    def has_organization_pattern(self, line):
        """Check if line contains organization-like patterns"""
        # Use spaCy if available
        if hasattr(self, 'nlp') and self.nlp:
            doc = self.nlp(line)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PERSON']:
                    return True
        
        # Check for common company suffixes
        company_suffixes = [
            'inc', 'corp', 'ltd', 'llc', 'company', 'corporation',
            'limited', 'enterprises', 'solutions', 'systems', 'technologies',
            'services', 'group', 'associates', 'partners', 'consulting'
        ]
        
        line_lower = line.lower()
        return any(suffix in line_lower for suffix in company_suffixes)

    def parse_job_line(self, line):
        """Parse job title, company name, and dates from a line"""
        import re
        
        # Initialize result
        result = {
            'job_title': '',
            'company_name': '',
            'location': '',
            'start_date': '',
            'enddate': '',
            'currentwork': False
        }
        
        # Try different separator patterns
        separators = ['@', '|', '–', ' - ', ' at ', ' with ', ' for ', ',']
        
        parts = []
        used_separator = None
        
        for sep in separators:
            if sep in line:
                parts = line.split(sep, 1)
                used_separator = sep
                break
        
        # If no separator found, try to split by common patterns
        if not parts:
            # Look for pattern like "Title CompanyName" where CompanyName has org indicators
            words = line.split()
            for i in range(1, len(words)):
                potential_company = ' '.join(words[i:])
                if self.has_organization_pattern(potential_company):
                    parts = [' '.join(words[:i]), potential_company]
                    break
        
        if len(parts) >= 2:
            raw_job_title = parts[0].strip()
            raw_company_part = parts[1].strip()
            
            # Extract job title
            result['job_title'] = self.validate_job_title(raw_job_title)
            
            # Extract company name from the company part (might contain dates)
            result['company_name'] = self.extract_company_from_part(raw_company_part)
            
            # Extract dates from the entire line
            date_info = self.extract_dates_from_line(line)
            result.update(date_info)
        
        return result

    def validate_job_title(self, raw_title):
        """Validate and clean job title"""
        if not raw_title or len(raw_title.strip()) < 3:
            return ''
        
        # Remove common prefixes
        cleaned = raw_title.strip('•-*0123456789. ')
        
        # Check if it contains actual job title words
        has_job_title = any(title.lower() in cleaned.lower() for title in self.job_titles)
        
        # Check length and word count constraints
        words = cleaned.split()
        if len(words) > 6 or len(cleaned) > 50:  # Too long to be a job title
            return ''
        
        # If it has job title keywords or reasonable length, accept it
        if has_job_title or (2 <= len(words) <= 4 and len(cleaned) > 5):
            return cleaned
        
        return ''

    def extract_company_from_part(self, company_part):
        """Extract company name from a part that might contain dates"""
        import re
        
        # Remove dates from the company part
        # Remove common date patterns
        cleaned = re.sub(r'\b\d{4}\b', '', company_part)  # Remove years
        cleaned = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', cleaned)  # Remove date formats
        cleaned = re.sub(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b(present|current|ongoing)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[(),\[\]{}]', ' ', cleaned)  # Remove brackets
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Clean whitespace
        
        # Validate company name
        if len(cleaned) < 2:
            return ''
        
        words = cleaned.split()
        if len(words) > 5:  # Too long to be a company name
            return ''
        
        # Use spaCy to validate if it's an organization
        if hasattr(self, 'nlp') and self.nlp:
            doc = self.nlp(cleaned)
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    return cleaned
        
        # Check for organization patterns
        if self.has_organization_pattern(cleaned):
            return cleaned
        
        # If reasonable length, accept it
        if 2 <= len(words) <= 4 and len(cleaned) > 3:
            return cleaned
        
        return ''

    def extract_dates_from_line(self, line):
        """Extract date information from line"""
        result = {
            'start_date': '',
            'enddate': '',
            'currentwork': False
        }
        
        # Check for current work indicators
        if any(word in line.lower() for word in ['present', 'current', 'ongoing']):
            result['currentwork'] = True
        
        # Extract dates using existing date patterns
        date_matches = []
        for pattern in self.date_patterns:
            date_matches.extend(pattern.findall(line))
        
        if date_matches:
            result['start_date'] = self.parse_date(str(date_matches[0]))
            if len(date_matches) >= 2:
                result['enddate'] = self.parse_date(str(date_matches[1]))
        
        return result

    def is_valid_experience(self, experience):
        """Check if experience entry is valid (has both job title and company)"""
        return (experience.get('job_title') and 
                experience.get('company_name') and
                experience.get('job_title').strip() != '' and 
                experience.get('company_name').strip() != '')


    def looks_like_date_line(self, line):
        line = line.strip().lower()

        # Common patterns: Mar 2025 - May 2025, March 2023 to Present, etc.
        date_range_patterns = [
            r'^[a-z]{3,9}\s+\d{4}\s*[-–to]+\s*[a-z]{3,9}\s+\d{4}$',   # Mar 2022 – May 2023
            r'^[a-z]{3,9}\s+\d{4}\s*[-–to]+\s*(present|current)$',    # May 2023 – Present
            r'^\d{4}\s*[-–to]+\s*\d{4}$',                             # 2021 – 2023
            r'^[a-z]{3,9}\s+\d{4}$',                                  # Just "Mar 2023"
            r'^\d{4}$'                                                # Just "2023"
        ]
        
        for pattern in date_range_patterns:
            if re.fullmatch(pattern, line):
                return True
        
        return False



    def extract_education(self, text):
        """Extract education information"""
        education = []
        
        # Find education section
        lines = text.split('\n')
        in_education_section = False
        education_lines = []
        
        for line in lines:
            if self.section_patterns['education'].search(line):
                in_education_section = True
                continue
            elif in_education_section and any(self.section_patterns[section].search(line) 
                                            for section in self.section_patterns if section != 'education'):
                break
            elif in_education_section:
                education_lines.append(line.strip())
        
        # Parse education entries
        current_education = {}
        
        for line in education_lines:
            if not line:
                if current_education:
                    education.append(current_education)
                    current_education = {}
                continue
            
            # Check if line contains degree information
            if any(degree.lower() in line.lower() for degree in self.degree_types):
                if current_education:
                    education.append(current_education)
                
                current_education = {
                    'institution': '',
                    'city': '',
                    'degree': '',
                    'field_of_study': '',
                    'start_date': '',
                    'enddate': '',
                    'currentstudy': False,
                    'description': ''
                }
                
                # Extract degree and field of study
                for degree_type in self.degree_types:
                    if degree_type.lower() in line.lower():
                        degree_match = re.search(rf'{degree_type}[.\s]*(?:of\s+|in\s+)?([^,\n-]+)', line, re.IGNORECASE)
                        if degree_match:
                            current_education['degree'] = degree_type.upper()
                            current_education['field_of_study'] = degree_match.group(1).strip()
                        break
                
                # Extract institution
                parts = line.split(',')
                if len(parts) >= 2:
                    current_education['institution'] = parts[-2].strip()
                    current_education['city'] = parts[-1].strip()
                
                # Extract dates
                date_matches = []
                for pattern in self.date_patterns:
                    date_matches.extend(pattern.findall(line))
                
                if date_matches:
                    current_education['start_date'] = self.parse_date(str(date_matches[0]))
                    if len(date_matches) >= 2:
                        current_education['enddate'] = self.parse_date(str(date_matches[1]))
                    elif 'present' in line.lower() or 'current' in line.lower():
                        current_education['currentstudy'] = True
        
        if current_education:
            education.append(current_education)
        
        return education

    def extract_projects(self, text):
        """Extract project information"""
        
        projects = []
        
        # Find projects section
        lines = text.split('\n')
        in_projects_section = False
        project_lines = []
        
        for line in lines:
            if self.section_patterns['projects'].search(line):
                in_projects_section = True
                continue
            elif in_projects_section and any(self.section_patterns[section].search(line) 
                                        for section in self.section_patterns if section != 'projects'):
                if len(project_lines)<7:
                    continue
                else:
                    break
            elif in_projects_section:
                project_lines.append(line.strip())
        
        # Parse project entries
        current_project = {}
        description_lines = []
        i = 0
        
        while i < len(project_lines):
            line = project_lines[i]
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if this line is a project title (starts with bullet point, dash, asterisk, or number)
            # is_project_title = (line.startswith('•') or line.startswith('-') or 
            #                 line.startswith('*') or re.match(r'^\d+\.', line))
            is_project_title = (line.startswith(('•', '-', '*')) or re.match(r'^\d+\.', line) or (line.isupper() and len(line.split()) <= 10) or 
                                (len(line.split()) <= 6 and len(line) < 60) or any(kw in line.lower() for kw in ['project', 'developed', 'created']))
            
            if is_project_title:
                # Save previous project if exists
                if current_project:
                    if description_lines:
                        current_project['project_description'] = '\n'.join(description_lines)
                    projects.append(current_project)
                
                # Start new project
                current_project = {
                    'project_name': '',
                    'institution': '',
                    'start_date': '',
                    'end_date': '',
                    'currentdo': False,
                    'project_description': ''
                }
                description_lines = []
                
                # Check for description delimiter in the same line (: | - etc.)
                delimiters = [':', '|', ' - ', ' – ', ' — ']
                title_and_desc = line.strip('•-*0123456789. ')
                
                found_delimiter = False
                for delimiter in delimiters:
                    if delimiter in title_and_desc:
                        parts = title_and_desc.split(delimiter, 1)
                        current_project['project_name'] = parts[0].strip()
                        if len(parts) > 1 and parts[1].strip():
                            description_lines.append(parts[1].strip())
                        found_delimiter = True
                        break
                
                # If no delimiter found, entire line is the title
                if not found_delimiter:
                    current_project['project_name'] = title_and_desc
                
                # Extract institution using spaCy NER
                current_project['institution'] = self.extract_institution_from_line(line, self.nlp)
                
                # Extract dates from project line
                date_matches = []
                for pattern in self.date_patterns:
                    date_matches.extend(pattern.findall(line))
                
                if date_matches:
                    current_project['start_date'] = self.parse_date(str(date_matches[0]))
                    if len(date_matches) >= 2:
                        current_project['end_date'] = self.parse_date(str(date_matches[1]))
                    elif 'present' in line.lower() or 'ongoing' in line.lower():
                        current_project['currentdo'] = True
                
                # Look for description in subsequent lines
                j = i + 1
                while j < len(project_lines):
                    next_line = project_lines[j].strip()
                    
                    # Stop if we hit an empty line or another project title
                    if not next_line:
                        break
                    
                    # Check if next line is another project title
                    is_next_project = (next_line.startswith('•') or next_line.startswith('-') or 
                                    next_line.startswith('*') or re.match(r'^\d+\.', next_line))
                    
                    if is_next_project:
                        break
                    
                    # Check for delimiter in description line
                    found_desc_delimiter = False
                    for delimiter in delimiters:
                        if delimiter in next_line:
                            desc_part = next_line.split(delimiter, 1)
                            if len(desc_part) > 1:
                                description_lines.append(desc_part[1].strip())
                            found_desc_delimiter = True
                            break
                    
                    # If no delimiter, add entire line as description
                    if not found_desc_delimiter:
                        description_lines.append(next_line)
                    
                    j += 1
                
                # Skip the lines we've already processed
                i = j - 1
            
            i += 1
        
        # Add the last project
        if current_project:
            if description_lines:
                current_project['project_description'] = '\n'.join(description_lines)
            projects.append(current_project)
        
        return projects

    def extract_institution_from_line(self, line, nlp):
        """Extract institution from a line using spaCy NER"""
        # Process the line with spaCy
        doc = nlp(line)
        
        # Look for organizations (ORG) and geopolitical entities (GPE)
        institutions = []
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'GPE']:
                institutions.append(ent.text)
        
        # Also check for common institution keywords
        institution_keywords = [
            'university', 'college', 'institute', 'school', 'academy',
            'corporation', 'company', 'inc', 'ltd', 'llc', 'foundation',
            'organization', 'association', 'society', 'lab', 'laboratory',
            'hospital', 'medical center', 'clinic', 'research center',
            'department', 'faculty', 'bureau', 'agency', 'ministry'
        ]
        
        # Split line into words and check for institution patterns
        words = line.lower().split()
        potential_institutions = []
        
        for i, word in enumerate(words):
            # Check if word contains institution keywords
            for keyword in institution_keywords:
                if keyword in word:
                    # Try to capture the full institution name
                    # Look for 2-4 words before and after the keyword
                    start_idx = max(0, i - 3)
                    end_idx = min(len(words), i + 4)
                    
                    # Extract potential institution phrase
                    potential_inst = ' '.join(words[start_idx:end_idx])
                    
                    # Clean up common prefixes/suffixes
                    potential_inst = potential_inst.strip('•-*0123456789. ()[]{}')
                    
                    # Remove dates and common non-institution words
                    cleaned_words = []
                    for w in potential_inst.split():
                        if not any(char.isdigit() for char in w) and \
                        w.lower() not in ['at', 'in', 'for', 'with', 'the', 'a', 'an', 'and', 'or']:
                            cleaned_words.append(w)
                    
                    if len(cleaned_words) >= 1:
                        potential_institutions.append(' '.join(cleaned_words))
                    break
        
        # Combine spaCy results with keyword-based results
        all_institutions = institutions + potential_institutions
        
        # Return the longest/most complete institution name found
        if all_institutions:
            # Remove duplicates and sort by length (longest first)
            unique_institutions = list(set(all_institutions))
            unique_institutions.sort(key=len, reverse=True)
            return unique_institutions[0]
        
        return ''
    
    def extract_languages(self, text):
        """Extract language information using predefined language and proficiency lists"""
        languages = []

        # Normalize language names for case-insensitive lookup
        language_map = {lang.lower(): lang for lang in self.languages}
        prof_levels = [p.lower() for p in self.proficiency_levels]

        # Find the languages section
        lines = text.split('\n')
        in_languages_section = False
        language_lines = []

        for line in lines:
            if self.section_patterns['languages'].search(line):
                in_languages_section = True
                language_lines.append(line.strip())
                continue
            elif in_languages_section and any(
                self.section_patterns[section].search(line)
                for section in self.section_patterns if section != 'languages'
            ):
                break
            elif in_languages_section:
                language_lines.append(line.strip())

        # Parse the entries
        for line in language_lines:
            if not line:
                continue

            # Split line into individual entries
            entries = re.split(r'[;|,\n]', line)
            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue

                entry_lower = entry.lower()
                found_language = ''
                found_proficiency = ''

                # Match proficiency level in entry
                for prof in prof_levels:
                    if prof in entry_lower:
                        found_proficiency = prof.capitalize()
                        # Remove from entry for cleaner language matching
                        entry_lower = entry_lower.replace(prof, '')

                # Clean entry further
                entry_lower = re.sub(r'[\(\)\[\]\-_:]', ' ', entry_lower).strip()

                # Match language name from known list
                for lang_key in language_map:
                    if lang_key in entry_lower:
                        found_language = language_map[lang_key]
                        break

                if found_language:
                    languages.append({
                        'language': found_language,
                        'proficiency': found_proficiency
                    })

        return languages

    def extract_certifications(self, text):
        certifications = []

        # Lowercased maps for fast lookup
        cert_map = {c.lower(): c for c in self.certifications}
        cert_keys = list(cert_map.keys())

        platform_map = {p.lower(): p for p in self.platforms}
        platform_keys = list(platform_map.keys())

        lines = text.split('\n')
        in_cert_section = False
        cert_lines = []

        # Collect lines from certifications section
        for line in lines:
            if self.section_patterns['certifications'].search(line):
                in_cert_section = True
                cert_lines.append(line.strip())
                continue
            elif in_cert_section and any(
                self.section_patterns[section].search(line)
                for section in self.section_patterns if section != 'certifications'
            ):
                break
            elif in_cert_section:
                cert_lines.append(line.strip())

        for line in cert_lines:
            if not line:
                continue

            line_clean = re.sub(r'[•\-*:()]', ' ', line).strip().lower()

            # Fuzzy match certification
            cert_match, cert_score, _ = process.extractOne(
                line_clean, cert_keys, scorer=fuzz.token_sort_ratio
            )
            if cert_score >= 70:
                matched_cert = cert_map[cert_match]
                start_date = ''
                end_date = ''

                # Fuzzy match platform
                platform_match, platform_score, _ = process.extractOne(
                    line_clean, platform_keys, scorer=fuzz.partial_ratio
                )
                platform = platform_map[platform_match] if platform_score >= 80 else ''

                # Extract date patterns
                date_matches = []
                for pattern in self.date_patterns:
                    date_matches.extend(pattern.findall(line))

                if date_matches:
                    start_date = self.parse_date(str(date_matches[0]))
                    if len(date_matches) >= 2:
                        end_date = self.parse_date(str(date_matches[1]))

                certifications.append({
                    'certificate_name': matched_cert,
                    'platform': platform,
                    'start_date': start_date,
                    'end_date': end_date
                })

        return certifications



    def extract_skills(self, text):
        """Extract general and job-specific skills from the resume text"""
        general_skills = set()
        job_specific_skills = set()
        
        # Find skills section
        lines = text.split('\n')
        in_skills_section = False
        skills_text = ''
        
        for line in lines:
            if self.section_patterns['skills'].search(line):
                in_skills_section = True
                continue
            elif in_skills_section and any(
                self.section_patterns[section].search(line) 
                for section in self.section_patterns if section != 'skills'
            ):
                break
            elif in_skills_section:
                skills_text += line + ' '
        
        # Normalize text
        skills_text_clean = re.sub(r'[^\w\s#+.-]', ' ', skills_text.lower())  # remove punctuations, keep tech symbols
        skills_text_lower = skills_text_clean.lower()
        
        # Normalize skill lists for case-insensitive matching
        general_skill_map = {s.lower(): s for s in self.general_skills}
        job_specific_skill_map = {s.lower(): s for s in self.job_specific_skills}
        
        # Match multi-word and single-word general skills
        for skill_lower, original_skill in general_skill_map.items():
            if skill_lower in skills_text_lower:
                general_skills.add(original_skill)

        # Match multi-word and single-word job-specific skills
        for skill_lower, original_skill in job_specific_skill_map.items():
            if skill_lower in skills_text_lower:
                job_specific_skills.add(original_skill)

        return list(general_skills), list(job_specific_skills)


    def extract_titles(self, text):
        """Extract primary, secondary, and tertiary titles"""
        lines = text.split('\n')
        titles = []
        
        # Look for potential titles in the first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if line and not self.email_pattern.search(line) and not any(pattern.search(line) for pattern in self.phone_patterns):
                # if any(title_word.lower() in line.lower() for title_word in self.job_titles):
                #     titles.append(title_word)
                for title_word in self.job_titles:
                    if title_word.lower() in line.lower():
                        titles.append(title_word.capitalize())
        
        # Fill in titles
        primary_title = titles[0] if len(titles) > 0 else ''
        secondary_title = titles[1] if len(titles) > 1 else ''
        tertiary_title = titles[2] if len(titles) > 2 else ''
        
        return primary_title, secondary_title, tertiary_title

    def extract_resume_data(self, file_path):
        """Main function to extract all resume data"""
        # Extract text from file
        try:
            text = self.extract_text_from_file(file_path)
            
            if not text:
                return None
            
            # Extract all information
            personal_info = self.extract_personal_info(text)
            links = self.extract_links(text)
            work_experience = self.extract_work_experience(text)
            education = self.extract_education(text)
            projects = self.extract_projects(text)
            languages = self.extract_languages(text)
            certifications = self.extract_certifications(text)
            general_skills, job_specific_skills = self.extract_skills(text)
            primary_title, secondary_title, tertiary_title = self.extract_titles(text)
            
            # Compile final result
            result = {
                **personal_info,
                'links': links,
                'work_experience': work_experience,
                'education': education,
                'projects': projects,
                'languages': languages,
                'certifications': certifications,
                'primary_title': primary_title,
                'secondary_title': secondary_title,
                'tertiary_title': tertiary_title,
                'generalSkills': general_skills,
                'jobSpecificSkills': job_specific_skills
            }
            
            return result
        except Exception as e:
            logger.error(f"Error extracting resume: {e}")
            return {"error": f"Error extracting resume: {str(e)}"}

# Usage example
# def main():
#     extractor = ResumeExtractor()
    
#     # Example usage
#     file_path = r"CV_06a8002b-6a11-4d1f-aa48-20071952c471(1).pdf"
    
#     try:
#         result = extractor.extract_resume_data(file_path)
        
#         if result:
#             print(json.dumps(result, indent=2, ensure_ascii=False))
            
#         else:
#             print("Failed to extract data from the resume.")
            
#     except Exception as e:
#         print(f"Error processing resume: {e}")

# if __name__ == "__main__":
#     main()