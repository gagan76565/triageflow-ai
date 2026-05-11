import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Load dataset
df = pd.read_csv("dataset.csv")

# Features and labels
X = df["text"]
y = df["category"]

# Create NLP pipeline
pipeline = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(stop_words="english")
    ),
    (
        "classifier",
        LogisticRegression(max_iter=1000)
    )
])

# Train model
pipeline.fit(X, y)

# Save trained model
joblib.dump(
    pipeline,
    "saved_models/ticket_classifier.pkl"
)

print("Model trained successfully!")