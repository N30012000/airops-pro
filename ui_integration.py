"""
UI Integration Module for Air Sial SMS v3.0
Handles OCR, file uploads, and UI enhancements
"""

import streamlit as st
import random
from datetime import datetime, timedelta, date


class OCRProcessor:
    """Mock OCR processor for form scanning"""
    
    @staticmethod
    def extract_text_from_image(image_file):
        """
        Mock OCR extraction from image
        In production, would use Tesseract or Google Vision API
        """
        # Simulate OCR processing
        extracted_data = {
            'confidence': random.randint(85, 98),
            'text_blocks': [
                'Flight Number: PF-101',
                'Aircraft: AP-BMA',
                'Date: ' + date.today().isoformat(),
                'Incident Description: Test incident from OCR'
            ],
            'fields_detected': 8,
            'processing_time_ms': random.randint(500, 2000)
        }
        return extracted_data
    
    @staticmethod
    def extract_form_fields(image_file, form_type: str):
        """
        Extract structured fields from form image
        
        Args:
            image_file: Uploaded image file
            form_type: Type of form (bird_strike, laser_strike, etc.)
        
        Returns:
            dict with extracted field values
        """
        
        # Mock extraction based on form type
        extraction_map = {
            'bird_strike': {
                'flight_number': 'PF-101',
                'aircraft_reg': 'AP-BMA',
                'incident_date': (date.today() - timedelta(days=random.randint(0, 7))).isoformat(),
                'incident_time': f"{random.randint(5, 22):02d}:{random.randint(0, 59):02d}",
                'bird_species': 'House Crow',
                'bird_size': 'Medium',
                'number_struck': 1,
                'damage_level': 'Minor',
                'narrative': 'Bird strike during climb out from Lahore'
            },
            'laser_strike': {
                'flight_number': 'PF-102',
                'aircraft_reg': 'AP-BMB',
                'incident_date': (date.today() - timedelta(days=random.randint(0, 7))).isoformat(),
                'incident_time': f"{random.randint(18, 23):02d}:{random.randint(0, 59):02d}",
                'laser_color': 'Green (532nm)',
                'laser_intensity': '2 - Moderate',
                'duration_seconds': random.randint(5, 30),
                'crew_effects': ['Distraction', 'Glare'],
                'narrative': 'Laser illumination during approach'
            },
            'tcas_report': {
                'flight_number': 'PF-103',
                'aircraft_reg': 'AP-BMC',
                'incident_date': (date.today() - timedelta(days=random.randint(0, 7))).isoformat(),
                'tcas_alert_type': 'RA - Climb',
                'altitude_fl': random.randint(250, 380),
                'ra_followed': 'Yes - Full compliance',
                'vertical_separation': random.randint(300, 1000),
                'narrative': 'TCAS RA received and followed correctly'
            },
            'hazard_report': {
                'hazard_date': (date.today() - timedelta(days=random.randint(0, 3))).isoformat(),
                'hazard_category': 'Aircraft Systems',
                'location': 'Ramp/Apron',
                'hazard_title': 'FOD observed on apron',
                'hazard_description': 'Foreign object debris observed during pre-flight inspection',
                'likelihood': 2,
                'severity': 'D',
                'suggested_actions': 'Enhanced FOD prevention procedures'
            }
        }
        
        return extraction_map.get(form_type, {})


def process_file_upload(uploaded_file) -> dict:
    """
    Process uploaded file (image, PDF, etc.)
    Extracts text and structures data
    
    Args:
        uploaded_file: Streamlit UploadedFile object
    
    Returns:
        dict with extracted data and metadata
    """
    
    if not uploaded_file:
        return {'status': 'error', 'message': 'No file uploaded'}
    
    try:
        file_type = uploaded_file.type
        file_name = uploaded_file.name
        file_size = uploaded_file.size
        
        # Determine file type and process accordingly
        if file_type.startswith('image/'):
            processor = OCRProcessor()
            extraction = processor.extract_text_from_image(uploaded_file)
            
            return {
                'status': 'success',
                'file_type': 'image',
                'file_name': file_name,
                'file_size': file_size,
                'confidence': extraction['confidence'],
                'text_blocks': extraction['text_blocks'],
                'fields_detected': extraction['fields_detected'],
                'processing_time_ms': extraction['processing_time_ms'],
                'extracted_at': datetime.now().isoformat()
            }
        
        elif file_type == 'application/pdf':
            return {
                'status': 'success',
                'file_type': 'pdf',
                'file_name': file_name,
                'file_size': file_size,
                'pages': random.randint(1, 5),
                'text_extracted': True,
                'extracted_at': datetime.now().isoformat()
            }
        
        else:
            return {
                'status': 'warning',
                'file_type': 'unknown',
                'message': 'File type not fully supported for OCR'
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'File processing failed: {str(e)}'
        }


def extract_form_data_from_upload(uploaded_file, form_type: str) -> dict:
    """
    Extract form fields from uploaded file
    Simulates OCR form parsing
    
    Args:
        uploaded_file: Uploaded image/PDF
        form_type: Type of safety form
    
    Returns:
        dict with extracted form fields
    """
    processor = OCRProcessor()
    return processor.extract_form_fields(uploaded_file, form_type)


def render_file_preview(uploaded_file):
    """Render preview of uploaded file in Streamlit"""
    
    if uploaded_file.type.startswith('image/'):
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
    elif uploaded_file.type == 'application/pdf':
        st.info(f"📄 PDF: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
    else:
        st.info(f"📎 File: {uploaded_file.name}")


def validate_form_data(data: dict, form_type: str) -> tuple:
    """
    Validate extracted or entered form data
    
    Args:
        data: Form data dictionary
        form_type: Type of form
    
    Returns:
        (is_valid: bool, errors: list)
    """
    
    errors = []
    
    # Common validations for all forms
    if not data.get('flight_number') and form_type != 'hazard_report':
        errors.append('Flight Number is required')
    
    if not data.get('date') and form_type == 'hazard_report':
        errors.append('Date is required')
    
    if not data.get('description') and not data.get('narrative'):
        errors.append('Description/Narrative is required')
    
    # Form-specific validations
    if form_type == 'bird_strike':
        if not data.get('bird_species'):
            errors.append('Bird species is required')
        if not data.get('damage_level'):
            errors.append('Damage level is required')
    
    elif form_type == 'laser_strike':
        if not data.get('laser_color'):
            errors.append('Laser color is required')
        if not data.get('laser_intensity'):
            errors.append('Laser intensity is required')
    
    elif form_type == 'tcas_report':
        if not data.get('tcas_alert_type'):
            errors.append('TCAS alert type is required')
    
    elif form_type == 'hazard_report':
        if not data.get('hazard_category'):
            errors.append('Hazard category is required')
        if not data.get('likelihood'):
            errors.append('Likelihood rating is required')
    
    return (len(errors) == 0, errors)


def get_extraction_confidence(data: dict) -> int:
    """
    Calculate confidence level of extracted data
    Based on completeness of fields
    
    Args:
        data: Extracted data dictionary
    
    Returns:
        Confidence percentage (0-100)
    """
    
    total_fields = len(data)
    filled_fields = sum(1 for v in data.values() if v)
    
    if total_fields == 0:
        return 0
    
    confidence = int((filled_fields / total_fields) * 100)
    return min(confidence, 100)  # Cap at 100
