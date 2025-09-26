from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
import pdfplumber


# Create your views here.


class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('pdf')
        if not pdf_file:
            return Response({'error': 'No file uploaded'}, status = 400)
        
        parsed_text = ' '
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                parsed_text += page.extract_text() or ''

        # ------- Grading logic / Length (15%) ---------------#
        word_count = len(parsed_text.split())
        if word_count < 100:
            grade += 5      # Too short
        elif word_count < 300:
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


        # Example grading logic
        if word_count < 100:
            grade += 5          # Too Short
        elif word_count < 300:
            grade = 70
        else:
            grade = 90

        # Check for important words:
        keyword = ["Python", "Django", "React", "AI", "Machine Learning"]
        keyword_hits = sum(1 for word in keyword if word.lower() in parsed_text.lower())

        grade += keyword_hits * 2

        # Ensure grade doesnot exceed 100
        grade = min(grade, 100)

        return Response({
            'text': parsed_text,
            'grade' : grade
        })


        return Response({'text': parsed_text})
           