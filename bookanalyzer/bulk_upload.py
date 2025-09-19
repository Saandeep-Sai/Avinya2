import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookanalyzer.settings')
django.setup()

from books.models import Book
from books.services.pdf_qa_service import PDFQAService

def bulk_upload_pdfs(pdf_directory):
    """Upload all PDFs from a directory"""
    pdf_qa = PDFQAService()
    
    for filename in os.listdir(pdf_directory):
        if filename.endswith('.pdf'):
            try:
                # Extract title from filename
                title = filename.replace('.pdf', '').replace('_', ' ')
                
                # Create book
                book = Book.objects.create(
                    title=title,
                    author="Unknown"
                )
                
                # Process PDF
                pdf_path = os.path.join(pdf_directory, filename)
                success = pdf_qa.build_index(book.id, pdf_path)
                
                if success:
                    book.is_indexed = True
                    book.save()
                    print(f"✅ {title} - Book ID: {book.id}")
                else:
                    print(f"❌ Failed to process: {title}")
                    
            except Exception as e:
                print(f"❌ Error with {filename}: {e}")

if __name__ == "__main__":
    # Usage: python bulk_upload.py
    pdf_dir = "path/to/your/pdf/folder"
    bulk_upload_pdfs(pdf_dir)