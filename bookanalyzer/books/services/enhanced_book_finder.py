import requests
import os
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

class EnhancedBookFinder:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def search_pdf_online(self, title, author):
        """Enhanced PDF search with multiple sources"""
        
        # Clean title and author for better search
        clean_title = self._clean_search_term(title)
        clean_author = self._clean_search_term(author)
        
        search_methods = [
            lambda: self._search_gutenberg(clean_title, clean_author),
            lambda: self._search_archive_org(clean_title, clean_author),
            lambda: self._search_openlibrary(clean_title, clean_author),
            lambda: self._search_google_books(clean_title, clean_author)
        ]
        
        for search_method in search_methods:
            try:
                pdf_url = search_method()
                if pdf_url:
                    print(f"Found PDF: {pdf_url}")
                    return pdf_url
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Search method failed: {e}")
                continue
        
        return None
    
    def _clean_search_term(self, term):
        """Clean search terms for better matching"""
        if not term or term.lower() == 'unknown':
            return ""
        return term.strip().replace("'", "").replace('"', '')
    
    def _search_gutenberg(self, title, author):
        """Search Project Gutenberg for free books"""
        try:
            if not title:
                return None
                
            query = f"{title} {author}".strip().replace(" ", "+")
            url = f"https://www.gutenberg.org/ebooks/search/?query={query}&submit_search=Go%21"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for PDF download links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '.pdf' in href and 'files' in href:
                        if href.startswith('/'):
                            return f"https://www.gutenberg.org{href}"
                        return href
            
            return None
        except Exception as e:
            print(f"Gutenberg search error: {e}")
            return None
    
    def _search_archive_org(self, title, author):
        """Search Internet Archive"""
        try:
            if not title:
                return None
                
            query = f"{title} {author}".strip().replace(" ", "%20")
            url = f"https://archive.org/search.php?query={query}&and[]=mediatype%3A%22texts%22"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for item links
                for link in soup.find_all('a', class_='stealth'):
                    if '/details/' in link['href']:
                        item_id = link['href'].split('/details/')[-1]
                        pdf_url = f"https://archive.org/download/{item_id}/{item_id}.pdf"
                        
                        # Check if PDF exists
                        pdf_check = requests.head(pdf_url, timeout=5)
                        if pdf_check.status_code == 200:
                            return pdf_url
            
            return None
        except Exception as e:
            print(f"Archive.org search error: {e}")
            return None
    
    def _search_openlibrary(self, title, author):
        """Search Open Library"""
        try:
            if not title:
                return None
                
            query = f"{title} {author}".strip()
            url = f"https://openlibrary.org/search.json?title={query}&limit=5"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for book in data.get('docs', []):
                    if 'ia' in book:  # Internet Archive identifier
                        ia_id = book['ia'][0] if isinstance(book['ia'], list) else book['ia']
                        pdf_url = f"https://archive.org/download/{ia_id}/{ia_id}.pdf"
                        
                        # Verify PDF exists
                        pdf_check = requests.head(pdf_url, timeout=5)
                        if pdf_check.status_code == 200:
                            return pdf_url
            
            return None
        except Exception as e:
            print(f"OpenLibrary search error: {e}")
            return None
    
    def _search_google_books(self, title, author):
        """Search Google Books API for free books"""
        try:
            if not title:
                return None
                
            query = f"{title} {author}".strip()
            url = f"https://www.googleapis.com/books/v1/volumes?q={query}&filter=free-ebooks&maxResults=5"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', []):
                    volume_info = item.get('volumeInfo', {})
                    access_info = item.get('accessInfo', {})
                    
                    if access_info.get('pdf', {}).get('isAvailable'):
                        pdf_url = access_info.get('pdf', {}).get('downloadLink')
                        if pdf_url:
                            return pdf_url
            
            return None
        except Exception as e:
            print(f"Google Books search error: {e}")
            return None
    
    def download_pdf(self, pdf_url, filename):
        """Download PDF with better error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,*/*'
            }
            
            response = requests.get(pdf_url, headers=headers, stream=True, timeout=60)
            
            if response.status_code == 200:
                os.makedirs("media/temp", exist_ok=True)
                filepath = f"media/temp/{filename}"
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify it's a valid PDF
                if os.path.getsize(filepath) > 1000:  # At least 1KB
                    return filepath
                else:
                    os.unlink(filepath)
                    return None
            
            return None
        except Exception as e:
            print(f"Download error: {e}")
            return None