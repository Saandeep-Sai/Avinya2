from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from books.models import Book, Chat
# Import services lazily to avoid initialization errors
import json
import os

# Initialize services lazily to avoid import errors
ocr_service = None
pdf_qa_service = None

def get_ocr_service():
    global ocr_service
    if ocr_service is None:
        from books.services.ocr_service import OCRService
        ocr_service = OCRService()
    return ocr_service

def get_pdf_qa_service():
    global pdf_qa_service
    if pdf_qa_service is None:
        from books.services.pdf_qa_service import PDFQAService
        pdf_qa_service = PDFQAService()
    return pdf_qa_service

@api_view(['POST'])
def upload_cover(request):
    """Upload book cover and extract details using OCR"""
    try:
        print("Upload cover request received")
        
        cover_image = request.FILES.get('cover_image')
        if not cover_image:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Image received: {cover_image.name}")
        
        # Save image
        image_path = default_storage.save(f'covers/{cover_image.name}', cover_image)
        full_path = os.path.join('media', image_path)
        
        print(f"Image saved to: {full_path}")
        
        # Extract text and identify book using Gemini Vision
        try:
            ocr = get_ocr_service()
            gemini_response = ocr.extract_text_from_cover(full_path)
            print(f"Gemini response: {gemini_response}")
        except Exception as ocr_error:
            print(f"OCR Error: {ocr_error}")
            # Fallback - create book with filename
            filename = cover_image.name.replace('.jpg', '').replace('.png', '').replace('.jpeg', '')
            book = Book.objects.create(
                title=filename or 'Unknown Book',
                author='Unknown Author',
                cover_image=image_path,
                extracted_text='OCR failed'
            )
            return Response({
                'book_id': book.id,
                'title': book.title,
                'author': book.author,
                'status': 'needs_pdf',
                'message': 'Image uploaded but recognition failed. Please upload PDF manually.',
                'is_indexed': False
            })
        
        # Parse Gemini response
        try:
            details = json.loads(gemini_response)
        except:
            details = {'title': 'Unknown Book', 'author': 'Unknown Author'}
        
        # Ensure we have valid title and author
        title = details.get('title', 'Unknown Book') or 'Unknown Book'
        author = details.get('author', 'Unknown Author') or 'Unknown Author'
        
        # Create book record
        book = Book.objects.create(
            title=title,
            author=author,
            cover_image=image_path,
            extracted_text=gemini_response
        )
        
        print(f"Book created: {book.title} by {book.author}")
        
        # Try auto-search for PDF (simplified)
        try:
            from books.services.enhanced_book_finder import EnhancedBookFinder
            finder = EnhancedBookFinder()
            
            pdf_url = finder.search_pdf_online(book.title, book.author)
            
            if pdf_url:
                pdf_path = finder.download_pdf(pdf_url, f"book_{book.id}.pdf")
                
                if pdf_path:
                    pdf_qa = get_pdf_qa_service()
                    success = pdf_qa.build_index(book.id, pdf_path)
                    
                    if success:
                        book.is_indexed = True
                        book.save()
                        os.unlink(pdf_path)
                        
                        return Response({
                            'book_id': book.id,
                            'title': book.title,
                            'author': book.author,
                            'status': 'ready',
                            'message': f'✅ {book.title} is ready! PDF found and analyzed.',
                            'is_indexed': True
                        })
        except Exception as search_error:
            print(f"PDF search error: {search_error}")
        
        # Return book info for manual PDF upload
        return Response({
            'book_id': book.id,
            'title': book.title,
            'author': book.author,
            'status': 'needs_pdf',
            'message': f'📖 {book.title} recognized. Upload PDF to start asking questions.',
            'is_indexed': False
        })
        
    except Exception as e:
        print(f"Upload cover error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def upload_pdf(request):
    """Upload PDF file for a book"""
    try:
        pdf_file = request.FILES.get('pdf_file')
        book_id = request.data.get('book_id')
        
        if not pdf_file:
            return Response({'error': 'No PDF provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        if book_id:
            book = Book.objects.get(id=book_id)
        else:
            # Create new book if no book_id provided
            title = request.data.get('title', 'Unknown Book')
            author = request.data.get('author', 'Unknown Author')
            book = Book.objects.create(title=title, author=author)
        
        # Process PDF without saving permanently
        import tempfile
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
            temp_pdf_path = temp_file.name
        
        # Build index from temporary file
        pdf_qa = get_pdf_qa_service()
        success = pdf_qa.build_index(book.id, temp_pdf_path)
        
        # Delete temporary file
        os.unlink(temp_pdf_path)
        
        if success:
            book.is_indexed = True
            book.save()
        
        return Response({
            'book_id': book.id,
            'title': book.title,
            'indexed': book.is_indexed
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def ask_question(request):
    """Ask question about a book"""
    try:
        book_id = request.data.get('book_id')
        question = request.data.get('question')
        
        if not book_id or not question:
            return Response({'error': 'book_id and question required'}, status=status.HTTP_400_BAD_REQUEST)
        
        book = Book.objects.get(id=book_id)
        
        # Get answer
        pdf_qa = get_pdf_qa_service()
        answer = pdf_qa.ask_question(book_id, question)
        
        # Save chat
        chat = Chat.objects.create(
            book=book,
            question=question,
            answer=answer
        )
        
        return Response({
            'question': question,
            'answer': answer,
            'chat_id': chat.id
        })
        
    except Book.DoesNotExist:
        return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_books(request):
    """Get all books"""
    books = Book.objects.all()
    data = [{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'is_indexed': book.is_indexed,
        'created_at': book.created_at
    } for book in books]
    
    return Response(data)

@api_view(['GET'])
def get_chat_history(request, book_id):
    """Get chat history for a book"""
    try:
        book = Book.objects.get(id=book_id)
        chats = Chat.objects.filter(book=book)[:20]
        
        data = [{
            'question': chat.question,
            'answer': chat.answer,
            'created_at': chat.created_at
        } for chat in chats]
        
        return Response(data)
        
    except Book.DoesNotExist:
        return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def search_books(request):
    """Search books by title or author"""
    query = request.GET.get('query', '')
    
    books = Book.objects.filter(
        title__icontains=query
    ) | Book.objects.filter(
        author__icontains=query
    )
    
    data = [{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'is_indexed': book.is_indexed
    } for book in books]
    
    return Response(data)

@api_view(['POST'])
def check_code_plagiarism(request):
    """Check if code is AI-generated or human-written"""
    try:
        code = request.data.get('code')
        if not code:
            return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        from books.services.ai_code_plagiarism_checker import AICodePlagiarismChecker
        checker = AICodePlagiarismChecker()
        
        result = checker.analyze_code(code)
        
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def batch_check_plagiarism(request):
    """Check multiple code snippets for plagiarism"""
    try:
        code_snippets = request.data.get('code_snippets', [])
        if not code_snippets:
            return Response({'error': 'No code snippets provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        from books.services.ai_code_plagiarism_checker import AICodePlagiarismChecker
        checker = AICodePlagiarismChecker()
        
        result = checker.batch_analyze(code_snippets)
        
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_book_status(request, book_id):
    """Get book indexing status"""
    try:
        book = Book.objects.get(id=book_id)
        chunks_path = f"media/indexes/book_{book_id}_chunks.pkl"
        
        return Response({
            'book_id': book.id,
            'title': book.title,
            'author': book.author,
            'is_indexed': book.is_indexed,
            'chunks_file_exists': os.path.exists(chunks_path),
            'chunks_path': chunks_path,
            'note': 'PDFs are processed and deleted - only text chunks stored'
        })
        
    except Book.DoesNotExist:
        return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
def clear_all_books(request):
    """Delete all books and their files"""
    try:
        # Delete all book records
        count = Book.objects.count()
        Book.objects.all().delete()
        
        # Clean up files
        import shutil
        try:
            shutil.rmtree('media/covers')
            shutil.rmtree('media/pdfs')
            shutil.rmtree('media/indexes')
        except:
            pass
        
        # Recreate directories
        os.makedirs('media/covers', exist_ok=True)
        os.makedirs('media/pdfs', exist_ok=True)
        os.makedirs('media/indexes', exist_ok=True)
        
        return Response({'message': f'Deleted {count} books and cleaned up files'})
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
