import os
import pdfplumber

def load_resumes_and_labels(folder_path):
    texts, labels = [], []
    for file in os.listdir(folder_path):
        if file.endswith('.pdf'):
            with pdfplumber.open(os.path.join(folder_path, file)) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
                texts.append(text)
                score = int(file.split('_')[-1].replace('.pdf', ''))
                labels.append(score)
    return texts, labels