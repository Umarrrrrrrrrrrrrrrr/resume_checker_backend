from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import pdfplumber


# Create your views here.


class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)   # File upload handling

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('pdf')             # retrives the uploaded file with the key "pdf"
        if not pdf_file:
            return Response({'error': 'No file uploaded'}, status = 400)        # If no file, it returns error 
        
        parsed_text = ' '                           # extract text from PDF
        with pdfplumber.open(pdf_file) as pdf:         # Uses pdfplumber to read each page of the uploaded PDF
            for page in pdf.pages:
                parsed_text += page.extract_text() or ''        # All pages text is concatenated into parsed_text



        # Initialize grade
        grade = 0           #  The grading starts with 0

        # ------- Grading logic / Length (15%) ---------------#
        word_count = len(parsed_text.split())
        if word_count < 50:
            grade += 5      # Too short
        elif word_count < 200:
            grade += 10     # Average
        else: 
            grade += 15     # Well-detailed

        # 2.Keywords / Technical skills (25%)
        keywords = ["Python", "Django", "React", "AI", "Machine Learning", "JavaScript", "SQL", "AWS", "TeamWork", "Leadership"]
        keyword_hits = sum(1 for word in keywords if word.lower() in parsed_text.lower())
        grade += min(keyword_hits * 2.5, 25)    # Cap at 25%

        # 3. Structure check (20%)
        sections = ["Education", "Experience", "Skills", "Projects", "Certifications", "Summary"]
        sections_hits = sum(1 for section in sections if section.lower() in parsed_text.lower())
        grade += min(sections_hits * 4, 20)
        
        # 4. Achievements / Action verbs    (15%)
        action_verbs = ["developed", "designed", "managed", "led", "built", "implemented", "achieved", "created"]
        action_hits = sum(1 for verb in action_verbs if verb.lower() in parsed_text.lower())
        grade += min(action_hits * 2, 15)


        # 5. professionalism (10%)
        if "@" in parsed_text:          # Email present
            grade += 5
        if "linkedin" in parsed_text.lower():
            grade += 15

        # 6. Overall Balance (15%)
        if 300 <= word_count <= 1000 and sections_hits >= 3:
            grade += 15

        # Ensure grade doesnot exceed 100
        grade = min(int(grade), 100)

        # -------------------------Response--------------------
        return Response({
            'text': parsed_text,
            'grade': grade,
            'word_count': word_count,
            'keyword_hits': keyword_hits,
            'sections_found': sections_hits,
            'action_words': action_hits
        })
        


        # # Example grading logic
        # if word_count < 100:
        #     grade += 5          # Too Short
        # elif word_count < 300:
        #     grade = 70
        # else:
        #     grade = 90

        # # Check for important words:
        # keyword = ["Python", "Django", "React", "AI", "Machine Learning"]
        # keyword_hits = sum(1 for word in keyword if word.lower() in parsed_text.lower())

        # grade += keyword_hits * 2

        # # Ensure grade doesnot exceed 100
        # grade = min(grade, 100)

        # return Response({
        #     'text': parsed_text,
        #     'grade' : grade
        # })


        # return Response({'text': parsed_text})
           