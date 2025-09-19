import os
import pickle
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

class PDFQAService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""
    
    def create_chunks(self, text, chunk_size=500):
        """Split text into chunks for indexing"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    
    def build_index(self, book_id, pdf_path):
        """Store PDF text chunks (simplified without FAISS)"""
        try:
            # Extract text and create chunks
            text = self.extract_text_from_pdf(pdf_path)
            chunks = self.create_chunks(text)
            
            # Save chunks only
            chunks_path = f"media/indexes/book_{book_id}_chunks.pkl"
            with open(chunks_path, 'wb') as f:
                pickle.dump(chunks, f)
                
            return True
        except Exception as e:
            print(f"Index building error: {e}")
            return False
    
    def ask_question(self, book_id, question):
        """Answer question about the book using Gemini"""
        try:
            # Load chunks
            chunks_path = f"media/indexes/book_{book_id}_chunks.pkl"
            
            print(f"Looking for chunks at: {chunks_path}")
            print(f"File exists: {os.path.exists(chunks_path)}")
            
            if not os.path.exists(chunks_path):
                return f"Book not indexed yet. Expected file: {chunks_path}. Please upload the PDF first."
            
            with open(chunks_path, 'rb') as f:
                chunks = pickle.load(f)
            
            print(f"Loaded {len(chunks)} chunks")
            
            # Use first few chunks as context (simplified)
            context = "\n".join(chunks[:5])
            
            # Generate answer using Gemini
            prompt = f"""
            Based on the following content from the book, answer the question.
            
            Book Content: {context}
            
            Question: {question}
            
            Answer:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"QA error: {e}")
            return f"Error: {str(e)}"