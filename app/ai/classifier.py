import joblib
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "training",
    "saved_models",
    "ticket_classifier.pkl"
)

# Load trained model once
model = joblib.load(MODEL_PATH)

def predict_category(text):

    prediction = model.predict([text])[0]

    probabilities = model.predict_proba([text])[0]

    confidence = max(probabilities) * 100

    return {
        "category": prediction,
        "confidence": round(confidence, 2)
    }