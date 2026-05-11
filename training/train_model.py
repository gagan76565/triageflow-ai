import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Load dataset
df = pd.read_csv("dataset.csv")

X = df["text"]
y = df["category"]

# Improved pipeline
pipeline = Pipeline([

    (
        "tfidf",

        TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000
        )
    ),

    (
        "classifier",

        LogisticRegression(
            max_iter=2000,
            C=2.0
        )
    )
])

# Train model
pipeline.fit(X, y)

# Save model
joblib.dump(
    pipeline,
    "saved_models/ticket_classifier.pkl"
)

print("Improved model trained successfully!")