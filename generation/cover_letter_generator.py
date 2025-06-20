from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
import os
import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

font_path1 = os.path.join(os.path.dirname(__file__), '../fonts/dejavu-sans.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', font_path1))

font_path2 = os.path.join(os.path.dirname(__file__), '../fonts/LibreBaskerville-Regular.ttf')
pdfmetrics.registerFont(TTFont('LibreBaskerville', font_path2))

font_path3 = os.path.join(os.path.dirname(__file__), '../fonts/LibreBaskerville-Bold.ttf')
pdfmetrics.registerFont(TTFont('LibreBaskerville-Bold', font_path3))

font_path5 = os.path.join(os.path.dirname(__file__), '../fonts/CormorantGaramond-VariableFont_wght.ttf')
pdfmetrics.registerFont(TTFont('CormorantGaramond', font_path5))

class CoverLetterGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Base styles - font sizes will be dynamically adjusted
        self.styles.add(ParagraphStyle(
            name='Name_Centered',
            fontName='LibreBaskerville-Bold',
            fontSize=30,  # This will be adjusted dynamically
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='Designation',
            fontName='LibreBaskerville-Bold',
            fontSize=20,  # This will be adjusted dynamically
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='Body_Paragraph',
            fontName='CormorantGaramond',
            fontSize=15,
            leading=17,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='Signature',
            fontName='LibreBaskerville',
            fontSize=15,
            leading=14,
            alignment=TA_LEFT,
            spaceBefore=30
        ))
        self.styles.add(ParagraphStyle(
            name='Footer',
            fontName='LibreBaskerville',
            fontSize=11,  # This will be adjusted dynamically
            leading=15,
            alignment=TA_LEFT,
            spaceBefore=30
        ))
        self.styles.add(ParagraphStyle(
            name='Contact_Info',
            fontName='LibreBaskerville',
            fontSize=13,  # This will be adjusted dynamically
            leading=16,
            alignment=TA_LEFT,
            firstLineIndent=0,
            leftIndent=0
        ))
    
    def calculate_dynamic_font_size(self, text, font_name, max_width, max_font_size, min_font_size=8):
        """
        Calculate the optimal font size to fit text within the given width
        
        Args:
            text: The text to measure
            font_name: The font family name
            max_width: Maximum width available (in points)
            max_font_size: Starting/maximum font size
            min_font_size: Minimum allowable font size
        
        Returns:
            Optimal font size that fits the text within max_width
        """
        font_size = max_font_size
        
        while font_size >= min_font_size:
            text_width = stringWidth(text, font_name, font_size)
            if text_width <= max_width:
                return font_size
            font_size -= 1
        
        return min_font_size
    
    def create_dynamic_style(self, base_style_name, text, max_width, font_name=None):
        """
        Create a new style with dynamically calculated font size
        
        Args:
            base_style_name: Name of the base style to copy from
            text: Text that needs to fit
            max_width: Maximum width available
            font_name: Optional font name override
        
        Returns:
            New ParagraphStyle with adjusted font size
        """
        base_style = self.styles[base_style_name]
        
        # Use provided font_name or default to base style's font
        font_to_use = font_name or base_style.fontName
        
        # Calculate optimal font size
        optimal_font_size = self.calculate_dynamic_font_size(
            text, 
            font_to_use, 
            max_width, 
            base_style.fontSize
        )
        
        # Create new style with adjusted font size
        new_style = ParagraphStyle(
            name=f'{base_style_name}_Dynamic',
            parent=base_style,
            fontSize=optimal_font_size,
            leading=optimal_font_size + 2  # Adjust leading proportionally
        )
        
        return new_style

    def create_contact_line(self, icon, text):
        """Create a properly formatted contact line with aligned icon and text"""
        return f'<para autoLeading="off" leftIndent="0" firstLineIndent="0"><font name="DejaVuSans">{icon}</font><font name="LibreBaskerville"> {text}</font></para>'

    def generate_cover_letter(self, data, output_filename=None):
        if output_filename is None:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    leftMargin=0.5*inch, rightMargin=0.5*inch,
                                    topMargin=0.5*inch, bottomMargin=0.5*inch)
        else:
            doc = SimpleDocTemplate(output_filename, pagesize=A4,
                                    leftMargin=0.5*inch, rightMargin=0.5*inch,
                                    topMargin=0.5*inch, bottomMargin=0.5*inch)

        # Calculate available widths
        page_width = A4[0] - (0.5*inch * 2)  # Total width minus margins
        left_column_width = 3.5 * inch
        right_column_width = 3.0 * inch
        
        story = []

        story.append(HRFlowable(width="100%", color=colors.black, thickness=0.8, spaceBefore=0, spaceAfter=5))

        # Create dynamic styles for name and designation
        name_style = self.create_dynamic_style(
            'Name_Centered', 
            data['user_details']['name'], 
            left_column_width
        )
        
        designation_style = self.create_dynamic_style(
            'Designation', 
            data['user_details']['designation'], 
            left_column_width
        )
        
        name_para = Paragraph(f"{data['user_details']['name']}", name_style)
        desig_para = Paragraph(f"{data['user_details']['designation']}", designation_style)

        # Create contact information with dynamic font sizing
        contact_paragraphs = []
        
        if data['user_details'].get('email'):
            email_style = self.create_dynamic_style(
                'Footer',
                data['user_details']['email'],
                right_column_width
            )
            contact_paragraphs.append([Paragraph(data['user_details']['email'], email_style)])
            
        if data['user_details'].get('contact'):
            contact_style = self.create_dynamic_style(
                'Footer',
                data['user_details']['contact'],
                right_column_width
            )
            contact_paragraphs.append([Paragraph(data['user_details']['contact'], contact_style)])
            
        if data['user_details'].get('address'):
            contact_paragraphs.append([Paragraph(data['user_details']['address'], self.styles['Footer'])])
        
        # Create left column with name and designation
        left_column = [name_para, desig_para]
        
        # Create right column with properly spaced and aligned contact information
        right_column_table = Table(contact_paragraphs, colWidths=[right_column_width])
        right_column_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        desired_height = 1.5 * inch # adjust based on your layout needs

        contact_table_data = [[left_column, '', right_column_table]]
        contact_table = Table(contact_table_data, colWidths=[left_column_width, 0.2 * inch, right_column_width], rowHeights=[desired_height])
        contact_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # Middle align both columns vertically
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        story.append(contact_table)

        story.append(HRFlowable(width="100%", color=colors.black, thickness=0.8, spaceBefore=5, spaceAfter=15))
        
        # Opening greeting
        story.append(Paragraph("To whom it may concern,", self.styles['Body_Paragraph']))
        
        # Body paragraphs
        for para in data['paragraphs']:
            story.append(Paragraph(para, self.styles['Body_Paragraph']))

        # Closing
        story.append(Paragraph("Yours sincerely,", self.styles['Body_Paragraph']))
        story.append(Paragraph(data['user_details']['name'], self.styles['Signature']))

        # Footer: title, email, phone, address
        story.append(Spacer(1, 0.5 * inch))

        story.append(HRFlowable(width="100%", color=colors.black, thickness=0.8, spaceBefore=10, spaceAfter=10))

        # Build the PDF
        doc.build(story)

        if output_filename is None:
            buffer.seek(0)
            return buffer
        else:
            logger.info(f"Cover letter saved to {output_filename}")
            return output_filename
    
    def save_document(self, doc_or_buffer, filename):
        """Save document to file"""
        try:
            # Make sure the directory exists
            directory = os.path.basename(filename)
            
            # If it's a BytesIO buffer, write its contents to file
            if isinstance(doc_or_buffer, BytesIO):
                with open(filename, 'wb') as f:
                    f.write(doc_or_buffer.getvalue())
                logger.info(f"Successfully saved buffer to {filename}")
            else:
                # If it's already a filename, just return it
                logger.info(f"File already saved as {doc_or_buffer}")
                return doc_or_buffer
                
            return filename
        except Exception as e:
            logger.error(f"Error saving {filename}: {str(e)}")
            raise