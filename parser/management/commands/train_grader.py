from django.core.management.base import BaseCommand
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import os

class Command(BaseCommand):
    help = 'Train resume grading model'

    def handle(self, **kwargs):
        folder_path = 'media/resumes'
        texts, labels = load_resumes_and_labels(folder_path)

        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        X = vectorizer.fit_transform(texts)

        x_train, x_test, y_train, y_test = train_test_split(x, labels, test_sizes= 0.2, random_state=42)

        model = Ridge()
        model.fit(x_train, y_train)

        preds = model.predict(x_test)
        mse = mean_squared_error(y_test, preds)
        self.stdout.write(self.style.SUCCESS(f'Model trained. MSE: {mse:.2f}'))

        os.makedirs('model', exist_ok=True)
        joblib.dump(model, 'model/resume_grader.pkl')
        joblib.dump(vectorizer, 'model/Tfidf_vectorizer.pkl')