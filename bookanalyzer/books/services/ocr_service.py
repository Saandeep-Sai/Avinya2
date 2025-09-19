from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

class OCRService:
    def __init__(self):
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise Exception('GEMINI_API_KEY not found in environment')
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            print(f"OCR Service init error: {e}")
            self.model = None

    def extract_text_from_cover(self, image_path):
        """Extract text from book cover using Gemini Vision"""
        try:
            if not self.model:
                raise Exception("Gemini model not initialized")
                
            # Load image
            image = Image.open(image_path)
            
            # Simple prompt
            prompt = "What is the title and author of this book? Return as JSON: {\"title\": \"book title\", \"author\": \"author name\"}"
            
            response = self.model.generate_content([prompt, image])
            result = response.text.strip()
            
            # Clean up response
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            
            # Validate JSON
            import json
            json.loads(result)  # Test if valid JSON
            
            return result
            
        except Exception as e:
            print(f"Gemini Vision Error: {e}")
            return '{"title": "Unknown Book", "author": "Unknown Author"}'

    def identify_book_details(self, gemini_response):
        """Parse Gemini Vision response (already contains book details)"""
        return gemini_response