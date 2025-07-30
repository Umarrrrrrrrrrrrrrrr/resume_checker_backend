from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FromParser


# Create your views here.


class ResumeUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('pdf')
        if not pdf_file:
            return response({'error': 'No file uploaded'}, status = 400)
        
        parsed_text = ' '
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                parsed_text += page.extract_text() or ''

        return Response({'text': parsed_text})
           