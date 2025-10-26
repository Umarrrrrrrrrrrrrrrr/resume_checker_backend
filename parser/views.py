from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import pdfplumber
import requests
import json
import re

class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('pdf')
        if not pdf_file:
            return Response({'error': 'No file uploaded'}, status=400)

        # Step 1: Extract text from PDF
        parsed_text = ''
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ''
                    parsed_text += page_text + "\n"
                    
            print(f"📄 Extracted {len(parsed_text)} characters from PDF")
            
            if len(parsed_text.strip()) == 0:
                return Response({
                    'error': 'No text could be extracted from the PDF.'
                }, status=400)
                
        except Exception as e:
            return Response({'error': f'PDF parsing error: {str(e)}'}, status=400)

        # Step 2: Prepare optimized prompt for stablelm-zephyr
        # Limit text length to avoid overwhelming the model
        resume_preview = parsed_text[:800]  # Smaller context for stable model
        
        prompt = f"""
        You are a professional HR resume analyzer. Analyze this resume content and provide feedback.

        RESUME CONTENT:
        {resume_preview}

        Provide your analysis in this exact JSON format only:
        {{
            "grade": 75,
            "summary": "Brief summary of the resume quality",
            "strengths": ["Good structure", "Relevant experience"],
            "weaknesses": ["Could use more metrics", "Skills section needs improvement"],
            "improvement_suggestions": "Add quantifiable achievements and expand technical skills section."
        }}

        Important: Return ONLY the JSON object, no additional text or explanations.
        Grade should be between 0-100 based on: clarity, relevance, completeness, and professionalism.
        """

        try:
            print(f"🤖 Using model: stablelm-zephyr...")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "stablelm-zephyr",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent JSON
                        "top_p": 0.9,
                        "num_ctx": 2048,     # Smaller context window
                    }
                },
                timeout=120  # Longer timeout for stablelm-zephyr
            )

            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                ai_response = response.json()
                ai_response_text = ai_response.get("response", "")
                
                print(f"✅ stablelm-zephyr responded! Response length: {len(ai_response_text)}")
                print(f"📋 Raw response preview: {ai_response_text[:200]}...")
                
                # Enhanced JSON extraction for stablelm-zephyr
                json_text = self.extract_json_from_response(ai_response_text)
                
                if json_text:
                    try:
                        ai_data = json.loads(json_text)
                        print(f"🎯 Successfully parsed JSON from stablelm-zephyr")
                        
                        # Process grade with validation
                        grade = self.process_grade(ai_data.get("grade", 50))
                        
                        return Response({
                            'grade': grade,
                            'summary': ai_data.get("summary", "Resume analysis completed successfully."),
                            'strengths': ai_data.get("strengths", ["Content properly formatted"]),
                            'weaknesses': ai_data.get("weaknesses", ["No critical issues found"]),
                            'improvement_suggestions': ai_data.get("improvement_suggestions", "Consider adding more quantifiable achievements."),
                            'text': parsed_text[:500] + "..." if len(parsed_text) > 500 else parsed_text,
                            'model_used': 'stablelm-zephyr',
                            'status': 'success'
                        })
                        
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON parsing error: {str(e)}")
                        print(f"📋 Problematic JSON: {json_text[:200]}")
                        return self.get_fallback_response(parsed_text, "JSON parsing failed")
                
                else:
                    print(f"⚠️ No JSON found in response")
                    # Try to extract any numerical score from the response
                    grade = self.extract_grade_from_text(ai_response_text)
                    return Response({
                        'grade': grade,
                        'summary': "AI analysis completed. Using extracted score.",
                        'strengths': ["Resume format acceptable"],
                        'weaknesses': ["Detailed analysis unavailable"],
                        'improvement_suggestions': "Ensure your resume includes clear sections for experience, education, and skills.",
                        'text': parsed_text[:500] + "..." if len(parsed_text) > 500 else parsed_text,
                        'model_used': 'stablelm-zephyr',
                        'status': 'partial',
                        'raw_ai_response': ai_response_text[:1000]  # For debugging
                    })
            
            else:
                error_msg = f"Model error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return Response({
                    'error': 'AI model is not responding properly.',
                    'details': 'Please check if stablelm-zephyr is installed and running.'
                }, status=500)
                
        except requests.exceptions.Timeout:
            print(f"⏰ stablelm-zephyr timeout")
            return Response({
                'error': 'AI analysis timed out. The model is taking too long to respond.'
            }, status=504)
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection error - Ollama not running?")
            return Response({
                'error': 'Cannot connect to AI service. Please ensure Ollama is running on localhost:11434'
            }, status=503)
        except Exception as e:
            print(f"💥 stablelm-zephyr error: {str(e)}")
            return self.get_fallback_response(parsed_text, str(e))

    def extract_json_from_response(self, text):
        """Enhanced JSON extraction for stablelm-zephyr responses"""
        # Method 1: Try to find JSON between curly braces
        json_match = re.search(r'\{[^{}]*\}', text)
        if json_match:
            return json_match.group()
        
        # Method 2: Try to find the main JSON object
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx+1]
        
        return None

    def process_grade(self, grade):
        """Process and validate the grade value"""
        if isinstance(grade, int):
            return max(0, min(100, grade))
        elif isinstance(grade, str):
            try:
                # Extract numbers from string like "85/100" or "Score: 75"
                numbers = re.findall(r'\d+', grade)
                if numbers:
                    return max(0, min(100, int(numbers[0])))
            except:
                pass
        return 50  # Default fallback grade

    def extract_grade_from_text(self, text):
        """Extract a grade from text response when JSON fails"""
        # Look for patterns like "85/100", "score: 75", etc.
        patterns = [
            r'grade[:\s]*(\d+)',
            r'score[:\s]*(\d+)',
            r'(\d+)/100',
            r'(\d+) out of 100',
            r'rating[:\s]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    grade = int(match.group(1))
                    return max(0, min(100, grade))
                except:
                    continue
        
        return 50  # Default grade

    def get_fallback_response(self, parsed_text, error_msg):
        """Provide a fallback response when AI analysis fails"""
        # Simple heuristic grading based on content
        word_count = len(parsed_text.split())
        sections = ["experience", "education", "skills", "projects"]
        sections_found = sum(1 for section in sections if section.lower() in parsed_text.lower())
        
        # Basic scoring logic
        base_score = min(70, word_count // 10)  # Up to 70 for length
        section_score = min(30, sections_found * 10)  # Up to 30 for sections
        
        total_score = base_score + section_score
        
        return Response({
            'grade': total_score,
            'summary': f"Basic analysis completed. (AI analysis failed: {error_msg})",
            'strengths': ["Document parsed successfully", "Basic structure detected"],
            'weaknesses': ["Detailed AI analysis unavailable", "Limited feedback provided"],
            'improvement_suggestions': "Consider adding clear sections for Experience, Education, Skills, and Projects.",
            'text': parsed_text[:500] + "..." if len(parsed_text) > 500 else parsed_text,
            'model_used': 'fallback',
            'status': 'fallback',
            'note': 'Using basic scoring due to AI model issues'
        })