import easyocr
import google.generativeai as genai
import os
from PIL import Image

class FallbackOCRService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.reader = easyocr.Reader(['en'])
    
    def extract_text_from_cover(self, image_path):
        """Extract text using EasyOCR + Gemini"""
        try:
            # First try EasyOCR
            results = self.reader.readtext(image_path)
            extracted_text = ' '.join([result[1] for result in results])
            
            # Then use Gemini to identify book details
            prompt = f"""
            From this text extracted from a book cover, identify the title and author:
            Text: {extracted_text}
            
            Return JSON: {{"title": "book title", "author": "author name"}}
            """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            
            return result
            
        except Exception as e:
            print(f"Fallback OCR Error: {e}")
            return '{"title": "Unknown", "author": "Unknown"}'