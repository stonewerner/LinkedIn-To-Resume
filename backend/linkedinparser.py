import fitz  # PyMuPDF
import json
import re
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from openai import OpenAI
from pinecone import Pinecone
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class DateRange:
    start: str
    end: str = "Present"

@dataclass
class Contact:
    name: str
    email: str
    location: str
    linkedin_url: str

@dataclass
class Experience:
    company: str
    title: str
    location: str
    dates: DateRange
    description: str

@dataclass
class Education:
    school: str
    degree: str
    field: str
    dates: DateRange

@dataclass
class Certification:
    name: str
    issuer: str
    date: str
    expires: str = ""

class LinkedInPDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.text = ""
        self.sections = {}
        
    def extract_text(self) -> None:
        """Extract text from PDF file."""
        try:
            doc = fitz.open(self.pdf_path)
            self.text = ""
            for page in doc:
                self.text += page.get_text()
            doc.close()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def identify_sections(self) -> None:
        """Split text into sections based on LinkedIn headers."""
        section_patterns = {
            'contact': r'Contact(.*?)(?=Experience|About|Education|$)',
            'summary': r'About(.*?)(?=Experience|Education|$)',
            'experience': r'Experience(.*?)(?=Education|Skills|$)',
            'education': r'Education(.*?)(?=Skills|Certifications|$)',
            'skills': r'Skills(.*?)(?=Languages|Certifications|$)',
            'certifications': r'Certifications(.*?)(?=Languages|$)',
            'languages': r'Languages(.*?)$'
        }

        # First pass to extract known sections
        for section, pattern in section_patterns.items():
            match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
            if match:
                self.sections[section] = match.group(1).strip()
            else:
                self.sections[section] = ""
        
        # Second pass to collect any unmatched content into "other"
        known_content = '|'.join(self.sections.values())
        remaining_text = re.sub(known_content, '', self.text, flags=re.DOTALL)
        self.sections['other'] = remaining_text.strip()

    def parse_contact(self) -> Contact:
        """Parse contact information section."""
        text = self.sections.get('contact', '')
        
        # Extract email using regex
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else ""
        
        # Extract name (usually first line)
        name = text.split('\n')[0].strip()
        
        # Extract location (usually contains city/country)
        location_match = re.search(r'(?:^|\n)([^,]+,\s*[^,]+)(?:$|\n)', text)
        location = location_match.group(1) if location_match else ""
        
        # Extract LinkedIn URL
        url_match = re.search(r'linkedin\.com/in/[\w-]+', text)
        linkedin_url = f"https://www.{url_match.group(0)}" if url_match else ""
        
        return Contact(name=name, email=email, location=location, linkedin_url=linkedin_url)

    def parse_experience(self) -> List[Experience]:
        """Parse work experience section."""
        experiences = []
        text = self.sections.get('experience', '')
        
        # Split into individual positions
        positions = re.split(r'\n(?=[A-Z][^a-z]*\n)', text)
        
        for position in positions:
            if not position.strip():
                continue
                
            lines = position.strip().split('\n')
            if len(lines) < 3:
                continue
                
            title = lines[0].strip()
            company = lines[1].strip()
            
            # Parse dates
            date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\s*-\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|Present)', position)
            dates = DateRange(
                start=date_match.group(1) if date_match else "",
                end=date_match.group(2) if date_match else ""
            )
            
            # Extract location
            location_match = re.search(r'(?:^|\n)([^,]+,\s*[^,]+)(?:$|\n)', position)
            location = location_match.group(1) if location_match else ""
            
            # Everything else is description
            description = '\n'.join(lines[3:]).strip()
            
            experiences.append(Experience(
                company=company,
                title=title,
                location=location,
                dates=dates,
                description=description
            ))
            
        return experiences

    def parse_education(self) -> List[Education]:
        """Parse education section."""
        education_list = []
        text = self.sections.get('education', '')
        
        # Split into individual education entries
        entries = re.split(r'\n(?=[A-Z][^a-z]*\n)', text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = entry.strip().split('\n')
            if len(lines) < 2:
                continue
            
            school = lines[0].strip()
            
            # Parse degree and field
            degree_field = lines[1].strip()
            degree_match = re.match(r'(.*?)\s+(?:in|,)\s+(.*)', degree_field)
            if degree_match:
                degree = degree_match.group(1).strip()
                field = degree_match.group(2).strip()
            else:
                degree = degree_field
                field = ""
            
            # Parse dates
            date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\s*-\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|Present)', entry)
            dates = DateRange(
                start=date_match.group(1) if date_match else "",
                end=date_match.group(2) if date_match else ""
            )
            
            education_list.append(Education(
                school=school,
                degree=degree,
                field=field,
                dates=dates
            ))
            
        return education_list

    def parse_certifications(self) -> List[Certification]:
        """Parse certifications section."""
        certifications = []
        text = self.sections.get('certifications', '')
        
        # Split into individual certifications
        entries = re.split(r'\n(?=[A-Z][^a-z]*\n)', text)
        
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = entry.strip().split('\n')
            if len(lines) < 2:
                continue
            
            name = lines[0].strip()
            issuer = lines[1].strip() if len(lines) > 1 else ""
            
            # Parse date
            date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', entry)
            date = date_match.group(1) if date_match else ""
            
            # Parse expiration date if exists
            expires_match = re.search(r'Expires?\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', entry)
            expires = expires_match.group(1) if expires_match else ""
            
            certifications.append(Certification(
                name=name,
                issuer=issuer,
                date=date,
                expires=expires
            ))
            
        return certifications

    def parse(self) -> Dict:
        """Main parsing method that returns structured JSON data."""
        try:
            self.extract_text()
            self.identify_sections()
            
            result = {
                'contact': asdict(self.parse_contact()),
                'summary': self.sections.get('summary', '').strip(),
                'experience': [asdict(exp) for exp in self.parse_experience()],
                'education': [asdict(edu) for edu in self.parse_education()],
                'skills': self.sections.get('skills', '').strip().split('\n'),
                'certifications': [asdict(cert) for cert in self.parse_certifications()],
                'languages': self.sections.get('languages', '').strip().split('\n'),
                'other': self.sections.get('other', '').strip()
            }
            
            # Clean up empty sections
            result = {k: v for k, v in result.items() if v}
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise

def profile_to_text(profile: Dict) -> str:
    """Convert profile sections to a single text for embedding"""
    text_parts = []
    
    # Add contact info
    if "contact" in profile:
        contact = profile["contact"]
        text_parts.append(f"Name: {contact.get('name', '')}")
        text_parts.append(f"Location: {contact.get('location', '')}")
    
    # Add summary
    if "summary" in profile:
        text_parts.append(f"Summary: {profile['summary']}")
    
    # Add experience
    if "experience" in profile:
        text_parts.append("Experience:")
        for exp in profile["experience"]:
            text_parts.append(
                f"{exp['title']} at {exp['company']} "
                f"({exp['dates']['start']} - {exp['dates']['end']})\n"
                f"{exp.get('description', '')}"
            )
    
    # Add education
    if "education" in profile:
        text_parts.append("Education:")
        for edu in profile["education"]:
            text_parts.append(
                f"{edu['degree']} in {edu['field']} from {edu['school']} "
                f"({edu['dates']['start']} - {edu['dates']['end']})"
            )
    
    # Add skills
    if "skills" in profile:
        text_parts.append(f"Skills: {', '.join(profile['skills'])}")
    
    # Add certifications
    if "certifications" in profile:
        text_parts.append("Certifications:")
        for cert in profile["certifications"]:
            text_parts.append(
                f"{cert['name']} from {cert['issuer']} "
                f"(Issued: {cert['date']}, Expires: {cert.get('expires', 'N/A')})"
            )
    
    return "\n\n".join(text_parts)

def store_profile_in_vector_db(profile: Dict, profile_id: str) -> bool:
    """Store parsed profile in vector database"""
    try:
        # Validate profile has required fields
        if not profile.get("contact"):
            raise ValueError("Profile missing contact information")
            
        # Initialize OpenAI and Pinecone clients
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index('linkedin-profiles')
        
        # Convert profile to text format
        text = profile_to_text(profile)
        
        # Generate embedding
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        embedding = response.data[0].embedding
        
        # Create vector record
        vector = {
            "values": embedding,
            "id": profile_id,  # Use validated ID
            "metadata": {
                "profile": json.dumps(profile),
                "text": text,
                "timestamp": datetime.utcnow().isoformat()  # Add timestamp for tracking
            }
        }
        
        # Upload to Pinecone
        result = index.upsert(
            vectors=[vector],
            namespace="profiles"
        )
        
        logger.info(f"Profile stored in vector database with ID: {profile_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing profile in vector database: {e}")
        return False

def retrieve_profile(profile_id: str) -> Optional[Dict]:
    """Retrieve a specific profile by ID."""
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index('linkedin-profiles')
        
        result = index.fetch(
            ids=[profile_id],
            namespace="profiles"
        )
        
        if not result.vectors:
            logger.warning(f"No profile found with ID: {profile_id}")
            return None
            
        # Parse stored JSON back to dict
        profile_data = json.loads(result.vectors[profile_id].metadata['profile'])
        return profile_data
        
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        return None

def find_similar_profiles(profile_id: str, top_k: int = 5) -> List[Dict]:
    """Find similar profiles to a given profile."""
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index('linkedin-profiles')
        
        # First get the vector for our target profile
        result = index.fetch(
            ids=[profile_id],
            namespace="profiles"
        )
        
        if not result.vectors:
            raise ValueError(f"No profile found with ID: {profile_id}")
            
        # Use the vector to find similar profiles
        query_response = index.query(
            vector=result.vectors[profile_id].values,
            top_k=top_k,
            namespace="profiles",
            include_metadata=True
        )
        
        # Convert results to list of profiles
        similar_profiles = []
        for match in query_response.matches:
            profile_data = json.loads(match.metadata['profile'])
            similar_profiles.append({
                'profile': profile_data,
                'score': match.score
            })
            
        return similar_profiles
        
    except Exception as e:
        logger.error(f"Error finding similar profiles: {e}")
        return []

def generate_resume(profile_id: str) -> Optional[Dict]:
    """Generate a resume for a given profile."""
    try:
        # 1. Retrieve the profile
        profile = retrieve_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")
            
        # 2. Find similar profiles for reference
        similar_profiles = find_similar_profiles(profile_id, top_k=3)
        
        # 3. Prepare context for AI
        context = {
            'target_profile': profile,
            'similar_profiles': similar_profiles,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 4. Generate resume content (placeholder for AI integration)
        # TODO: Integrate with your chosen AI model (e.g., Groq)
        resume_content = {
            'profile_id': profile_id,
            'context': context,
            # Add generated content here
        }
        
        return resume_content
        
    except Exception as e:
        logger.error(f"Error generating resume: {e}")
        return None

# Update parse_linkedin_pdf to return the profile ID
def parse_linkedin_pdf(pdf_path: str, store_in_db: bool = True) -> Tuple[str, Dict]:
    """Parse LinkedIn PDF and optionally store in vector database.
    Returns tuple of (profile_id, profile_data)"""
    try:
        # Parse PDF
        parser = LinkedInPDFParser(pdf_path)
        profile_data = parser.parse()
        profile_id = None
        
        # Store in vector database if requested
        if store_in_db:
            profile_id = f"profile_{uuid.uuid4()}"
            store_success = store_profile_in_vector_db(profile_data, profile_id)
            if not store_success:
                logger.warning("Failed to store profile in vector database")
        
        return profile_id, profile_data
        
    except Exception as e:
        logger.error(f"Failed to parse LinkedIn PDF: {e}")
        raise

# Example usage
if __name__ == "__main__":
    try:
        result = parse_linkedin_pdf("path/to/linkedin_profile.pdf")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Failed to parse LinkedIn PDF: {e}")