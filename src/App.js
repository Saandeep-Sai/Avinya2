import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import PlagiarismChecker from './PlagiarismChecker';
import './App.css';

const API_BASE = 'http://127.0.0.1:8000/api/books';

function App() {
  const [books, setBooks] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [currentPage, setCurrentPage] = useState('books'); // 'books' or 'plagiarism'

  // Fetch all books
  const fetchBooks = async () => {
    try {
      const response = await axios.get(API_BASE);
      setBooks(response.data);
    } catch (error) {
      console.error('Error fetching books:', error);
    }
  };

  // Upload cover image - complete workflow
  const uploadCover = async (file) => {
    setLoading(true);
    setUploadStatus('📸 Analyzing cover image...');
    
    const formData = new FormData();
    formData.append('cover_image', file);
    
    try {
      const response = await axios.post(`${API_BASE}/upload-cover/`, formData);
      
      if (response.data.is_indexed) {
        // Book ready for questions
        setUploadStatus(response.data.message);
        setSelectedBook(response.data);
      } else {
        // Need manual PDF upload
        setUploadStatus(response.data.message);
      }
      
      fetchBooks();
    } catch (error) {
      setUploadStatus('❌ Error: ' + error.message);
    }
    
    setLoading(false);
  };

  // Upload PDF directly or for recognized book
  const uploadPDF = async (file, bookId = null) => {
    setLoading(true);
    setUploadStatus('📄 Processing PDF and building RAG model...');
    
    const formData = new FormData();
    formData.append('pdf_file', file);
    if (bookId) formData.append('book_id', bookId);
    
    try {
      const response = await axios.post(`${API_BASE}/upload-pdf/`, formData);
      setUploadStatus('✅ PDF analyzed! Ready for questions.');
      
      // Auto-select the processed book
      if (response.data.indexed) {
        setSelectedBook(response.data);
      }
      
      fetchBooks();
    } catch (error) {
      setUploadStatus('❌ Error processing PDF: ' + error.message);
    }
    
    setLoading(false);
  };

  // Ask question
  const askQuestion = async () => {
    if (!selectedBook || !question.trim()) return;
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE}/ask-question/`, {
        book_id: selectedBook.book_id || selectedBook.id,
        question: question
      });
      
      setChatHistory(prev => [...prev, {
        question: question,
        answer: response.data.answer
      }]);
      
      setQuestion('');
    } catch (error) {
      console.error('Error asking question:', error);
    }
    
    setLoading(false);
  };

  // Dropzone for cover images
  const { getRootProps: getCoverProps, getInputProps: getCoverInputProps } = useDropzone({
    accept: { 'image/*': [] },
    onDrop: (files) => uploadCover(files[0])
  });

  // Dropzone for PDFs
  const { getRootProps: getPDFProps, getInputProps: getPDFInputProps } = useDropzone({
    accept: { 'application/pdf': [] },
    onDrop: (files) => uploadPDF(files[0], selectedBook?.book_id || selectedBook?.id)
  });

  useEffect(() => {
    fetchBooks();
  }, []);

  if (currentPage === 'plagiarism') {
    return <PlagiarismChecker />;
  }

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>📚 Book Analyzer</h1>
          <nav className="nav-buttons">
            <button 
              className={currentPage === 'books' ? 'active' : ''}
              onClick={() => setCurrentPage('books')}
            >
              📚 Book Analysis
            </button>
            <button 
              className={currentPage === 'plagiarism' ? 'active' : ''}
              onClick={() => setCurrentPage('plagiarism')}
            >
              🤖 Code Plagiarism
            </button>
          </nav>
        </div>
      </header>
      
      <div className="container">
        {/* Upload Section */}
        <div className="upload-section">
          <div className="upload-box" {...getCoverProps()}>
            <input {...getCoverInputProps()} />
            <p>📸 Upload Book Cover</p>
            <small>AI will recognize book → find PDF → analyze automatically</small>
          </div>
          
          <div className="upload-box" {...getPDFProps()}>
            <input {...getPDFInputProps()} />
            <p>📄 Upload PDF Directly</p>
            <small>Skip cover recognition - analyze PDF immediately</small>
          </div>
        </div>

        {/* Status */}
        {uploadStatus && (
          <div className="status">
            {uploadStatus}
          </div>
        )}

        {/* Books List */}
        <div className="books-section">
          <h3>Your Books ({books.length})</h3>
          <div className="books-grid">
            {books.map(book => (
              <div 
                key={book.id} 
                className={`book-card ${selectedBook?.id === book.id ? 'selected' : ''}`}
                onClick={() => setSelectedBook(book)}
              >
                <h4>{book.title}</h4>
                <p>by {book.author}</p>
                <span className={`status ${book.is_indexed ? 'ready' : 'pending'}`}>
                  {book.is_indexed ? '✅ Ready' : '⏳ Pending'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Section */}
        {selectedBook && selectedBook.is_indexed && (
          <div className="chat-section">
            <h3>Ask about: {selectedBook.title}</h3>
            
            <div className="chat-history">
              {chatHistory.map((chat, index) => (
                <div key={index} className="chat-item">
                  <div className="question">
                    <strong>You:</strong> {chat.question}
                  </div>
                  <div className="answer">
                    <strong>AI:</strong> {chat.answer}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="question-input">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about this book..."
                onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                disabled={loading}
              />
              <button onClick={askQuestion} disabled={loading || !question.trim()}>
                {loading ? '...' : 'Ask'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
