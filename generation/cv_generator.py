import logging
import json
import os
import re
import argparse
from reportlab.lib.pagesizes import LETTER, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

logger = logging.getLogger(__name__)

class ResumeTemplate:
    """Base class for resume templates"""
    def __init__(self, data, output_file="resume.pdf", pagesize=LETTER):
        self.user = data['user_details']
        self.content = data['content']
        self.doc = SimpleDocTemplate(output_file, pagesize=pagesize,
                            rightMargin=50, leftMargin=50, topMargin=30, bottomMargin=40)
        self.styles = getSampleStyleSheet()
        self.story = []
        self.setup_styles()
        
    def setup_styles(self):
        """Set up custom styles for the template"""
        pass
        
    def build(self):
        """Build the PDF document"""
        self.doc.build(self.story)
        
    def generate(self):
        """Generate the resume content"""
        pass

#font_path = os.path.join(os.path.dirname(__file__), '../fonts/dejavu-sans.ttf')
font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fonts/dejavu-sans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

class ClassicTemplate(ResumeTemplate):
    """Enhanced Classic resume template with improved design and Unicode icons"""

    def setup_styles(self):
        base_font = 'Times-Roman'
        self.styles.add(ParagraphStyle(name='TitleBold', fontSize=19, leading=22, spaceBefore=0, spaceAfter=10, textTransform='uppercase', fontName=base_font, alignment=1))  # Center align title
        self.styles.add(ParagraphStyle(name='Header', fontSize=15, leading=18, fontName=base_font, spaceAfter=6, textTransform='uppercase', textColor=colors.black, alignment=0)) 
        self.styles.add(ParagraphStyle(name='Designation', fontSize=13, leading=14, fontName=base_font, spaceAfter=2, alignment=1)) 
        self.styles.add(ParagraphStyle(name='SubHeader', fontSize=13, leading=14, fontName=base_font, spaceAfter=2, alignment=0)) 
        self.styles.add(ParagraphStyle(name='MyNormal', fontSize=11, leading=12, fontName=base_font, spaceAfter=4, alignment=4))  # Justified text
        self.styles.add(ParagraphStyle(name='CustomBullet', fontSize=11, leading=12, leftIndent=14, bulletIndent=6, fontName=base_font, alignment=4))  # Justified bullet points
        self.styles.add(ParagraphStyle(name='Meta', fontSize=10, leading=11, fontName=base_font, textColor=colors.grey, alignment=1)) 

    def icon_line(self, icon_char, text):
        """Embed a monochrome Unicode icon using DejaVuSans inline, followed by Times-Roman text"""
        return f'<font name="DejaVuSans">{icon_char}</font> <font name="Times-Roman">{text}</font>'

    def generate(self):
        # Header Section
        self.story.append(Paragraph(self.user['name'], self.styles['TitleBold']))
        self.story.append(Paragraph(self.user['designation'], self.styles['Designation']))
        self.story.append(Spacer(1, 4))

        # contact_line_1 = " | ".join([
        #     self.icon_line("✉", self.user['email']),
        #     self.icon_line("☎", self.user['contact'])
        # ])
        # contact_line_2 = " | ".join([
        #     self.icon_line("➤", self.user['linkedin']),
        #     self.icon_line("⚙", self.user['portfolio'])
        # ])
        # address_line = self.icon_line("⌂", self.user['address'])

        def safe_icon_line(symbol, value):
            return self.icon_line(symbol, value) if value else None

        contact_line_1 = " | ".join(filter(None, [
            safe_icon_line("✉", self.user.get('email')),
            safe_icon_line("☎", self.user.get('contact'))
        ]))

        contact_line_2 = " | ".join(filter(None, [
            safe_icon_line("➤", self.user.get('linkedin')),
            safe_icon_line("⚙", self.user.get('portfolio'))
        ]))

        address_line = safe_icon_line("⌂", self.user.get('address')) or ""


        self.story.append(Paragraph(contact_line_1, self.styles['Meta']))
        self.story.append(Paragraph(contact_line_2, self.styles['Meta']))
        self.story.append(Paragraph(address_line, self.styles['Meta']))
        self.story.append(HRFlowable(width="100%", color=colors.black, thickness=0.8, spaceBefore=10, spaceAfter=10))

        # Profile Summary Section
        self.story.append(Paragraph("Profile Summary", self.styles['Header']))
        self.story.append(Paragraph(self.content['summary'], self.styles['MyNormal']))
        self.story.append(Spacer(1, 10))

        # Education Section
        self.story.append(Paragraph("Education", self.styles['Header']))
        self.story.append(HRFlowable(width="100%", color=colors.black, thickness=0.5, spaceBefore=4, spaceAfter=6))
        for edu in self.user['education']:
            self.story.append(Paragraph(edu, self.styles['CustomBullet'], bulletText="•"))
        self.story.append(Spacer(1, 10))

        # Experience Section
        self.story.append(Paragraph("Experience", self.styles['Header']))
        self.story.append(HRFlowable(width="100%", color=colors.black, thickness=0.5, spaceBefore=4, spaceAfter=6))

        if self.content['experience_summary'] and isinstance(self.content['experience_summary'][0], dict):
            for exp in self.content['experience_summary']:
                period = exp['period']
                job_title = f"{exp['position']}, {exp['company_name']}"
                
                # Create a 2-column table: left = period, right = job title
                table_data = [[
                    Paragraph(job_title, self.styles['SubHeader']),
                    Paragraph(period, self.styles['SubHeader'])
                ]]
                
                table = Table(table_data, colWidths=[330, 150])  # Adjust widths as needed
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))

                self.story.append(table)

                # Description sentences with bullet points
                description_text = exp['description']
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', description_text)
                for sentence in sentences:
                    if sentence.strip():
                        self.story.append(Paragraph(sentence.strip(), self.styles['CustomBullet'], bulletText="•"))
                self.story.append(Spacer(1, 8))
        else:
            for exp in self.content['experience_summary']:
                self.story.append(Paragraph(exp, self.styles['CustomBullet'], bulletText="•"))
        self.story.append(Spacer(1, 10))

        # Certifications Section
        if self.user.get('certifications'):
            self.story.append(Paragraph("Certifications", self.styles['Header']))
            self.story.append(HRFlowable(width="100%", color=colors.black, thickness=0.5, spaceBefore=4, spaceAfter=6))
            for cert in self.user['certifications']:
                self.story.append(Paragraph(cert, self.styles['CustomBullet'], bulletText="•"))
            self.story.append(Spacer(1, 10))

        # Tech Stack Section
        if self.content.get('skills'):
            self.story.append(Paragraph("Skills", self.styles['Header']))
            self.story.append(HRFlowable(width="100%", color=colors.black, thickness=0.5, spaceBefore=4, spaceAfter=6))
            # tools = ', '.join(self.content['skills'])
            # self.story.append(Paragraph(tools, self.styles['MyNormal']))
            for skill in self.content['skills']:
                self.story.append(Paragraph(skill, self.styles['CustomBullet'], bulletText="•"))
            self.story.append(Spacer(1, 10))

        # Languages Section
        if self.user.get('languages'):
            self.story.append(Paragraph("Languages", self.styles['Header']))
            self.story.append(HRFlowable(width="100%", color=colors.black, thickness=0.5, spaceBefore=4, spaceAfter=6))
            for lang in self.user['languages']:
                self.story.append(Paragraph(lang, self.styles['CustomBullet'], bulletText="•"))

        self.build()

def get_available_templates():
    """Return a dictionary of available templates"""
    return {
        "classic": ClassicTemplate,
    }

class CVGenerator:
    def __init__(self):
        self.templates = {
            "classic": ClassicTemplate,
            # add more templates here if needed
        }

    def generate_cv(self, data, filename="resume.pdf", template_name="classic", pagesize="LETTER"):
        try:
            # Ensure output directory exists
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # Select template
            pagesize_enum = LETTER if pagesize == "LETTER" else A4
            template_class = self.templates.get(template_name, ClassicTemplate)
            template_instance = template_class(data, output_file=filename, pagesize=pagesize_enum)

            # Generate the PDF
            template_instance.generate()

            logger.info(f"✅ Resume generated and saved as {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Failed to generate resume: {str(e)}")
            raise