from pylatex import Document, Section, Subsection, Command, Package
from pylatex.utils import NoEscape, bold
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ResumeTheme:
    """Theme configuration for resume styling"""
    primary_color: str = 'black'
    accent_color: str = '0.5,0.5,0.5'  # RGB values
    font_family: str = 'helvetica'
    section_style: str = 'basic'  # 'basic', 'modern', or 'classic'
    layout: str = 'traditional'  # 'traditional' or 'modern'
    font_size: str = '11pt'

class ResumeGenerator:
    def __init__(self, profile_data: Dict, theme: Optional[ResumeTheme] = None):
        self.profile = profile_data
        self.theme = theme or ResumeTheme()
        self.doc = Document(
            documentclass='article',
            geometry_options={'margin': '0.7in'},
            font_size=self.theme.font_size
        )
        self._setup_document()

    def _setup_document(self):
        """Setup document with necessary packages and styling"""
        # Add required packages
        self.doc.packages.append(Package('hyperref'))
        self.doc.packages.append(Package('xcolor'))
        self.doc.packages.append(Package('enumitem'))
        self.doc.packages.append(Package('fontawesome'))
        
        # Add font packages based on theme
        if self.theme.font_family == 'helvetica':
            self.doc.packages.append(Package('helvet'))
            self.doc.preamble.append(Command('renewcommand', r'\familydefault', r'\sfdefault'))
        elif self.theme.font_family == 'times':
            self.doc.packages.append(Package('mathptmx'))
        
        # Define colors
        self.doc.preamble.append(Command('definecolor', 'primary', 'RGB', self.theme.primary_color))
        self.doc.preamble.append(Command('definecolor', 'accent', 'RGB', self.theme.accent_color))
        
        # Custom section styling
        if self.theme.section_style == 'modern':
            self.doc.preamble.append(NoEscape(r'''
                \titleformat{\section}
                {\color{primary}\Large\bfseries}
                {}{0em}
                {\color{primary}}[\color{accent}\titlerule]
            '''))
        elif self.theme.section_style == 'classic':
            self.doc.preamble.append(NoEscape(r'''
                \titleformat{\section}
                {\color{primary}\Large\bfseries}
                {}{0em}
                {\uppercase}
            '''))
        
        # Remove page numbers
        self.doc.preamble.append(Command('pagenumbering', 'gobble'))

    def _add_header(self):
        """Add contact information header"""
        contact = self.profile.get('contact', {})
        
        # Create header with name
        self.doc.append(NoEscape(r'\begin{center}'))
        self.doc.append(NoEscape(r'{\Large\textbf{' + contact.get('name', '') + r'}}\\[0.5em]'))
        
        # Add contact details
        contact_lines = []
        if contact.get('email'):
            contact_lines.append(rf'\faEnvelope\ {contact["email"]}')
        if contact.get('location'):
            contact_lines.append(rf'\faMapMarker\ {contact["location"]}')
        if contact.get('linkedin_url'):
            contact_lines.append(rf'\faLinkedin\ {contact["linkedin_url"]}')
            
        self.doc.append(NoEscape(' | '.join(contact_lines)))
        self.doc.append(NoEscape(r'\end{center}'))
        self.doc.append(NoEscape(r'\vspace{1em}'))

    def _add_summary(self):
        """Add professional summary section"""
        if summary := self.profile.get('summary'):
            with self.doc.create(Section('Professional Summary', numbering=False)):
                self.doc.append(summary)

    def _add_experience(self):
        """Add work experience section"""
        if experiences := self.profile.get('experience'):
            with self.doc.create(Section('Professional Experience', numbering=False)):
                for exp in experiences:
                    # Company and title header
                    self.doc.append(NoEscape(r'\textbf{' + exp['company'] + r'} \hfill ' + 
                                          exp['dates']['start'] + ' - ' + exp['dates']['end'] + r'\\'))
                    self.doc.append(NoEscape(r'\textit{' + exp['title'] + r'} \hfill ' + 
                                          exp['location'] + r'\\[0.5em]'))
                    
                    # Description
                    if exp.get('description'):
                        self.doc.append(NoEscape(r'\begin{itemize}[leftmargin=*]'))
                        for bullet in exp['description'].split('\n'):
                            if bullet.strip():
                                self.doc.append(NoEscape(r'\item ' + bullet.strip()))
                        self.doc.append(NoEscape(r'\end{itemize}'))
                    
                    self.doc.append(NoEscape(r'\vspace{1em}'))

    def _add_education(self):
        """Add education section"""
        if education := self.profile.get('education'):
            with self.doc.create(Section('Education', numbering=False)):
                for edu in education:
                    self.doc.append(NoEscape(r'\textbf{' + edu['school'] + r'} \hfill ' +
                                          edu['dates']['start'] + ' - ' + edu['dates']['end'] + r'\\'))
                    self.doc.append(NoEscape(r'\textit{' + edu['degree'] + 
                                          (' in ' + edu['field'] if edu.get('field') else '') + r'}\\'))
                    self.doc.append(NoEscape(r'\vspace{0.5em}'))

    def _add_skills(self):
        """Add skills section"""
        if skills := self.profile.get('skills'):
            with self.doc.create(Section('Skills', numbering=False)):
                self.doc.append(NoEscape(r'\begin{itemize}[leftmargin=*]'))
                for skill in skills:
                    self.doc.append(NoEscape(r'\item ' + skill))
                self.doc.append(NoEscape(r'\end{itemize}'))

    def _add_certifications(self):
        """Add certifications section"""
        if certifications := self.profile.get('certifications'):
            with self.doc.create(Section('Certifications', numbering=False)):
                for cert in certifications:
                    self.doc.append(NoEscape(r'\textbf{' + cert['name'] + r'} \hfill ' + cert['date'] + r'\\'))
                    if cert.get('issuer'):
                        self.doc.append(NoEscape(r'\textit{' + cert['issuer'] + r'}\\'))
                    self.doc.append(NoEscape(r'\vspace{0.5em}'))

    def generate(self, output_path: str) -> str:
        """Generate the resume and return the path to the PDF file"""
        try:
            # Add all sections based on layout
            if self.theme.layout == 'traditional':
                self._add_header()
                self._add_summary()
                self._add_experience()
                self._add_education()
                self._add_skills()
                self._add_certifications()
            elif self.theme.layout == 'modern':
                self._add_header()
                # Create two-column layout
                self.doc.append(NoEscape(r'\begin{minipage}[t]{0.3\textwidth}'))
                self._add_skills()
                self._add_education()
                self._add_certifications()
                self.doc.append(NoEscape(r'\end{minipage}\hfill'))
                self.doc.append(NoEscape(r'\begin{minipage}[t]{0.65\textwidth}'))
                self._add_summary()
                self._add_experience()
                self.doc.append(NoEscape(r'\end{minipage}'))
            
            # Generate PDF
            self.doc.generate_pdf(output_path, clean_tex=False)
            return f"{output_path}.pdf"
            
        except Exception as e:
            raise Exception(f"Failed to generate resume: {str(e)}")