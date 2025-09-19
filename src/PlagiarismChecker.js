import React, { useState } from 'react';
import axios from 'axios';
import './PlagiarismChecker.css';

const API_BASE = 'http://127.0.0.1:8000/api/books';

function PlagiarismChecker() {
  const [code, setCode] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [batchMode, setBatchMode] = useState(false);
  const [codeSnippets, setCodeSnippets] = useState(['']);

  const analyzeCode = async () => {
    if (!code.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/check-plagiarism/`, {
        code: code
      });
      setResult(response.data);
    } catch (error) {
      setResult({ error: 'Analysis failed: ' + error.message });
    }
    setLoading(false);
  };

  const analyzeBatch = async () => {
    const validSnippets = codeSnippets.filter(snippet => snippet.trim());
    if (validSnippets.length === 0) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/batch-check-plagiarism/`, {
        code_snippets: validSnippets
      });
      setResult(response.data);
    } catch (error) {
      setResult({ error: 'Batch analysis failed: ' + error.message });
    }
    setLoading(false);
  };

  const addSnippet = () => {
    setCodeSnippets([...codeSnippets, '']);
  };

  const removeSnippet = (index) => {
    setCodeSnippets(codeSnippets.filter((_, i) => i !== index));
  };

  const updateSnippet = (index, value) => {
    const updated = [...codeSnippets];
    updated[index] = value;
    setCodeSnippets(updated);
  };

  const getResultColor = (percentage) => {
    if (percentage > 70) return '#e74c3c';
    if (percentage > 50) return '#f39c12';
    return '#27ae60';
  };

  const sampleCodes = {
    human: `def fibonacci(n):
    if n <= 1:
        return n
    # I always forget the recursive formula lol
    return fibonacci(n-1) + fibonacci(n-2)

# Test it
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")`,
    
    ai: `def fibonacci(n):
    """
    Calculate the nth Fibonacci number using recursion.
    
    Args:
        n (int): The position in the Fibonacci sequence
        
    Returns:
        int: The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def main():
    """Main function to demonstrate Fibonacci calculation."""
    for i in range(10):
        result = fibonacci(i)
        print(f"Fibonacci({i}) = {result}")

if __name__ == "__main__":
    main()`
  };

  return (
    <div className="plagiarism-checker">
      <div className="header">
        <h1>🤖 AI Code Plagiarism Checker</h1>
        <p>Detect if code was written by AI or humans with confidence percentages</p>
      </div>

      <div className="mode-selector">
        <button 
          className={!batchMode ? 'active' : ''} 
          onClick={() => setBatchMode(false)}
        >
          Single Analysis
        </button>
        <button 
          className={batchMode ? 'active' : ''} 
          onClick={() => setBatchMode(true)}
        >
          Batch Analysis
        </button>
      </div>

      {!batchMode ? (
        <div className="single-mode">
          <div className="input-section">
            <div className="sample-buttons">
              <button onClick={() => setCode(sampleCodes.human)}>
                Load Human Sample
              </button>
              <button onClick={() => setCode(sampleCodes.ai)}>
                Load AI Sample
              </button>
              <button onClick={() => setCode('')}>
                Clear
              </button>
            </div>
            
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Paste your code here for analysis..."
              rows={15}
              className="code-input"
            />
            
            <button 
              onClick={analyzeCode} 
              disabled={loading || !code.trim()}
              className="analyze-btn"
            >
              {loading ? '🔍 Analyzing...' : '🔍 Analyze Code'}
            </button>
          </div>
        </div>
      ) : (
        <div className="batch-mode">
          <div className="batch-controls">
            <button onClick={addSnippet} className="add-snippet-btn">
              ➕ Add Code Snippet
            </button>
          </div>
          
          {codeSnippets.map((snippet, index) => (
            <div key={index} className="snippet-container">
              <div className="snippet-header">
                <h4>Code Snippet {index + 1}</h4>
                {codeSnippets.length > 1 && (
                  <button 
                    onClick={() => removeSnippet(index)}
                    className="remove-btn"
                  >
                    ❌
                  </button>
                )}
              </div>
              <textarea
                value={snippet}
                onChange={(e) => updateSnippet(index, e.target.value)}
                placeholder={`Code snippet ${index + 1}...`}
                rows={8}
                className="code-input"
              />
            </div>
          ))}
          
          <button 
            onClick={analyzeBatch} 
            disabled={loading || codeSnippets.every(s => !s.trim())}
            className="analyze-btn"
          >
            {loading ? '🔍 Analyzing Batch...' : '🔍 Analyze All Snippets'}
          </button>
        </div>
      )}

      {result && (
        <div className="results-section">
          {result.error ? (
            <div className="error-result">
              <h3>❌ Error</h3>
              <p>{result.error}</p>
            </div>
          ) : result.summary ? (
            // Batch results
            <div className="batch-results">
              <div className="summary-card">
                <h3>📊 Batch Analysis Summary</h3>
                <div className="summary-stats">
                  <div className="stat">
                    <span className="label">Total Snippets:</span>
                    <span className="value">{result.summary.total_snippets}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Analyzed:</span>
                    <span className="value">{result.summary.analyzed_snippets}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Likely AI:</span>
                    <span className="value" style={{color: '#e74c3c'}}>
                      {result.summary.likely_ai_count}
                    </span>
                  </div>
                  <div className="stat">
                    <span className="label">Likely Human:</span>
                    <span className="value" style={{color: '#27ae60'}}>
                      {result.summary.likely_human_count}
                    </span>
                  </div>
                </div>
                
                <div className="avg-percentages">
                  <div className="percentage-bar">
                    <div className="label">Average AI Probability</div>
                    <div className="bar">
                      <div 
                        className="fill ai-fill" 
                        style={{width: `${result.summary.average_ai_probability}%`}}
                      ></div>
                    </div>
                    <span className="percentage">{result.summary.average_ai_probability}%</span>
                  </div>
                  
                  <div className="percentage-bar">
                    <div className="label">Average Human Probability</div>
                    <div className="bar">
                      <div 
                        className="fill human-fill" 
                        style={{width: `${result.summary.average_human_probability}%`}}
                      ></div>
                    </div>
                    <span className="percentage">{result.summary.average_human_probability}%</span>
                  </div>
                </div>
              </div>

              <div className="individual-results">
                <h4>Individual Results</h4>
                {result.individual_results.map((res, index) => (
                  <div key={index} className="result-card">
                    <h5>Snippet {res.snippet_id}</h5>
                    {res.error ? (
                      <p className="error">{res.error}</p>
                    ) : (
                      <div className="result-content">
                        <div className="percentages">
                          <div className="ai-percentage">
                            <span>AI: {res.ai_probability}%</span>
                          </div>
                          <div className="human-percentage">
                            <span>Human: {res.human_probability}%</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            // Single result
            <div className="single-result">
              <div className="result-header">
                <h3>📊 Analysis Results</h3>
                <div className="confidence">
                  Confidence: {result.confidence}%
                </div>
              </div>

              <div className="percentage-display">
                <div className="percentage-card ai-card">
                  <div className="percentage-circle">
                    <div 
                      className="circle-fill" 
                      style={{
                        background: `conic-gradient(#e74c3c 0deg ${result.ai_probability * 3.6}deg, #ecf0f1 ${result.ai_probability * 3.6}deg 360deg)`
                      }}
                    >
                      <div className="circle-inner">
                        <span className="percentage-text">{result.ai_probability}%</span>
                      </div>
                    </div>
                  </div>
                  <h4>🤖 AI Generated</h4>
                </div>

                <div className="percentage-card human-card">
                  <div className="percentage-circle">
                    <div 
                      className="circle-fill" 
                      style={{
                        background: `conic-gradient(#27ae60 0deg ${result.human_probability * 3.6}deg, #ecf0f1 ${result.human_probability * 3.6}deg 360deg)`
                      }}
                    >
                      <div className="circle-inner">
                        <span className="percentage-text">{result.human_probability}%</span>
                      </div>
                    </div>
                  </div>
                  <h4>👨‍💻 Human Written</h4>
                </div>
              </div>

              <div className="analysis-details">
                <div className="reasoning">
                  <h4>🧠 Analysis Reasoning</h4>
                  <p>{result.reasoning}</p>
                </div>

                {result.indicators && (
                  <div className="indicators">
                    <div className="ai-indicators">
                      <h5>🤖 AI Indicators</h5>
                      <ul>
                        {result.indicators.ai_indicators?.map((indicator, index) => (
                          <li key={index}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="human-indicators">
                      <h5>👨‍💻 Human Indicators</h5>
                      <ul>
                        {result.indicators.human_indicators?.map((indicator, index) => (
                          <li key={index}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {result.code_stats && (
                  <div className="code-stats">
                    <h5>📈 Code Statistics</h5>
                    <div className="stats-grid">
                      <div className="stat">Lines: {result.code_stats.total_lines}</div>
                      <div className="stat">Non-empty: {result.code_stats.non_empty_lines}</div>
                      <div className="stat">Comments: {result.code_stats.comment_lines}</div>
                      <div className="stat">Characters: {result.code_stats.total_characters}</div>
                      <div className="stat">Functions: {result.code_stats.has_functions ? '✅' : '❌'}</div>
                      <div className="stat">Classes: {result.code_stats.has_classes ? '✅' : '❌'}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PlagiarismChecker;