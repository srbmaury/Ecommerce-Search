import joblib
import os

model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking_model.pkl")
model = None
if os.path.exists(model_path):
    model = joblib.load(model_path)

def predict_score(features):
    if model is not None:
        try:
            probas = model.predict_proba([features])
            # Validate that probas is indexable and has at least one row and two columns
            if (
                hasattr(probas, "__len__")
                and len(probas) > 0
                and hasattr(probas[0], "__len__")
                and len(probas[0]) > 1
            ):
                return float(probas[0][1])
        except Exception:
            # Any issue with prediction or shape falls through to the fallback
            pass
    # Fallback: use relevance (first feature) if model is missing or prediction fails
    return float(features[0])
