import google.generativeai as genai
import os
from PIL import Image
import base64
import io

class SimpleOCRService:
    """OCR service using Gemini Vision instead of Tesseract"""
    
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY', 'your-api-key-here'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def extract_text_from_cover(self, image_path):
        """Extract text from book cover using Gemini Vision"""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Use Gemini Vision to extract text
            prompt = """
            Extract all text from this book cover image. 
            Focus on the title and author name.
            Return the text exactly as you see it.
            """
            
            response = self.model.generate_content([prompt, image])
            return response.text.strip()
            
        except Exception as e:
            print(f"Gemini Vision OCR Error: {e}")
            return ""

    def identify_book_details(self, extracted_text):
        """Use Gemini to identify book title and author from OCR text"""
        try:
            prompt = f"""
            From this text extracted from a book cover, identify the book title and author.
            Return only in this JSON format:
            {{"title": "Book Title", "author": "Author Name"}}
            
            Extracted text: {extracted_text}
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")
            return '{"title": "Unknown", "author": "Unknown"}'