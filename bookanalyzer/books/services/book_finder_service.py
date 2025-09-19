import requests
import os
from bs4 import BeautifulSoup
import google.generativeai as genai

class BookFinderService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def search_pdf_online(self, title, author):
        """Search for PDF online using multiple sources"""
        search_sources = [
            self._search_libgen,
            self._search_archive_org,
            self._search_gutenberg
        ]
        
        for search_func in search_sources:
            try:
                pdf_url = search_func(title, author)
                if pdf_url:
                    return pdf_url
            except Exception as e:
                print(f"Search error: {e}")
                continue
        
        return None
    
    def _search_libgen(self, title, author):
        """Search Library Genesis"""
        try:
            query = f"{title} {author}".replace(" ", "+")
            url = f"http://libgen.rs/search.php?req={query}&lg_topic=libgen&open=0&view=simple&res=25&phrase=1&column=def"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Parse libgen results and extract PDF download link
                # This is a simplified example - actual implementation would be more complex
                links = soup.find_all('a', href=True)
                for link in links:
                    if 'download' in link['href'].lower() or '.pdf' in link['href'].lower():
                        return link['href']
            
            return None
        except:
            return None
    
    def _search_archive_org(self, title, author):
        """Search Internet Archive"""
        try:
            query = f"{title} {author}".replace(" ", "%20")
            url = f"https://archive.org/search.php?query={query}&and[]=mediatype%3A%22texts%22"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Parse archive.org results
                # Simplified implementation
                return None
            
            return None
        except:
            return None
    
    def _search_gutenberg(self, title, author):
        """Search Project Gutenberg for free books"""
        try:
            query = f"{title} {author}".replace(" ", "+")
            url = f"https://www.gutenberg.org/ebooks/search/?query={query}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse Gutenberg results for PDF links
                # Simplified implementation
                return None
            
            return None
        except:
            return None
    
    def download_pdf(self, pdf_url, filename):
        """Download PDF from URL"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                filepath = f"media/temp/{filename}"
                os.makedirs("media/temp", exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return filepath
            
            return None
        except Exception as e:
            print(f"Download error: {e}")
            return None