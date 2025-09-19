import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

class AICodePlagiarismChecker:
    def __init__(self):
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise Exception('GEMINI_API_KEY not found in environment')
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            print(f"AI Plagiarism Checker init error: {e}")
            self.model = None

    def analyze_code(self, code):
        """Analyze code to determine if it's AI-generated or human-written"""
        try:
            if not self.model:
                raise Exception("Gemini model not initialized")

            # Clean and validate code
            if not code or len(code.strip()) < 10:
                return {
                    'error': 'Code too short for analysis (minimum 10 characters)',
                    'ai_probability': 0,
                    'human_probability': 0
                }

            prompt = f"""
            Analyze the following code and determine if it was written by AI or a human programmer.
            
            Consider these factors:
            1. Code structure and patterns
            2. Variable naming conventions
            3. Comments style and frequency
            4. Code complexity and organization
            5. Common AI-generated code patterns
            6. Human coding habits and inconsistencies
            
            Code to analyze:
            ```
            {code}
            ```
            
            Return your analysis in this exact JSON format:
            {{
                "ai_probability": <percentage 0-100>,
                "human_probability": <percentage 0-100>,
                "confidence": <percentage 0-100>,
                "reasoning": "Brief explanation of your analysis",
                "indicators": {{
                    "ai_indicators": ["list", "of", "ai", "patterns"],
                    "human_indicators": ["list", "of", "human", "patterns"]
                }}
            }}
            """

            response = self.model.generate_content(prompt)
            result = response.text.strip()

            # Clean up response
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()

            # Parse JSON response
            import json
            analysis = json.loads(result)
            
            # Validate percentages
            ai_prob = max(0, min(100, analysis.get('ai_probability', 0)))
            human_prob = max(0, min(100, analysis.get('human_probability', 0)))
            
            # Normalize percentages to sum to 100
            total = ai_prob + human_prob
            if total > 0:
                ai_prob = (ai_prob / total) * 100
                human_prob = (human_prob / total) * 100
            else:
                ai_prob = 50
                human_prob = 50

            return {
                'ai_probability': round(ai_prob, 1),
                'human_probability': round(human_prob, 1),
                'confidence': analysis.get('confidence', 75),
                'reasoning': analysis.get('reasoning', 'Analysis completed'),
                'indicators': analysis.get('indicators', {
                    'ai_indicators': [],
                    'human_indicators': []
                }),
                'code_stats': self._get_code_stats(code)
            }

        except json.JSONDecodeError:
            return {
                'error': 'Failed to parse AI response',
                'ai_probability': 50,
                'human_probability': 50
            }
        except Exception as e:
            print(f"Code analysis error: {e}")
            return {
                'error': f'Analysis failed: {str(e)}',
                'ai_probability': 0,
                'human_probability': 0
            }

    def _get_code_stats(self, code):
        """Get basic statistics about the code"""
        lines = code.split('\n')
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'comment_lines': len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')]),
            'total_characters': len(code),
            'has_functions': bool(re.search(r'def\s+\w+|function\s+\w+|const\s+\w+\s*=', code)),
            'has_classes': bool(re.search(r'class\s+\w+', code)),
            'has_imports': bool(re.search(r'import\s+|from\s+\w+\s+import|#include|require\(', code))
        }

    def batch_analyze(self, code_snippets):
        """Analyze multiple code snippets"""
        results = []
        
        for i, code in enumerate(code_snippets):
            result = self.analyze_code(code)
            result['snippet_id'] = i + 1
            results.append(result)
        
        return {
            'individual_results': results,
            'summary': self._generate_summary(results)
        }

    def _generate_summary(self, results):
        """Generate summary statistics for batch analysis"""
        if not results:
            return {}
        
        valid_results = [r for r in results if 'error' not in r]
        
        if not valid_results:
            return {'error': 'No valid results to summarize'}
        
        avg_ai_prob = sum(r['ai_probability'] for r in valid_results) / len(valid_results)
        avg_human_prob = sum(r['human_probability'] for r in valid_results) / len(valid_results)
        avg_confidence = sum(r['confidence'] for r in valid_results) / len(valid_results)
        
        return {
            'total_snippets': len(results),
            'analyzed_snippets': len(valid_results),
            'average_ai_probability': round(avg_ai_prob, 1),
            'average_human_probability': round(avg_human_prob, 1),
            'average_confidence': round(avg_confidence, 1),
            'likely_ai_count': len([r for r in valid_results if r['ai_probability'] > 70]),
            'likely_human_count': len([r for r in valid_results if r['human_probability'] > 70])
        }