import os
import joblib
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

_MODEL: Optional[object] = None


def load_model() -> Optional[object]:
    """Load ranking model from disk if present."""
    model_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ranking_model.pkl",
    )

    if not os.path.exists(model_path):
        logger.warning("Ranking model not found at %s", model_path)
        return None

    try:
        logger.info("Loading ranking model from %s", model_path)
        return joblib.load(model_path)
    except Exception:
        logger.exception("Failed to load ranking model")
        return None


def get_model() -> Optional[object]:
    """Lazy-load model to avoid import-time side effects."""
    global _MODEL
    if _MODEL is None:
        _MODEL = load_model()
    return _MODEL


def predict_score(features: np.ndarray) -> float:
    """
    Predict ranking score for a single feature vector.

    Falls back to a heuristic score (first feature) if:
    - model is missing
    - prediction fails
    - output shape is unexpected
    """
    model = get_model()

    if model is not None:
        try:
            # LGBMRanker uses predict(), not predict_proba()
            scores = model.predict(np.asarray([features]))
            return float(scores[0])

        except Exception:
            logger.exception("Model prediction failed")

    # Fallback: heuristic relevance score
    fallback_score = float(features[0])
    logger.debug("Using fallback score: %f", fallback_score)
    return fallback_score
