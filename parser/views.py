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

        # ------- Simple Grading logic ---------------#
        word_count = len(parsed_text.split())

        # Example grading logic
        if word_count < 100:
            grade = 40
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
           