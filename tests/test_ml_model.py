"""Tests for ml/model.py — fallback scoring and prediction interface."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ml.features import build_features
from ml.model import predict_score


def _make_features(popularity=500, rating=4.0, days_old=30,
                   category_score=0.5, price_affinity=0.5):
    created = datetime.now(timezone.utc) - timedelta(days=days_old)
    return build_features(popularity, rating, created, category_score, price_affinity)


class TestPredictScoreFallback:
    """When no model is loaded, predict_score uses the heuristic formula."""

    def setup_method(self):
        # Force no model so tests don't depend on a .pkl file being present
        self._patch = patch("ml.model._MODEL", None)
        self._patch.start()
        # Also patch load_model to return None so it doesn't try to load from disk
        self._patch2 = patch("ml.model.load_model", return_value=None)
        self._patch2.start()

    def teardown_method(self):
        self._patch.stop()
        self._patch2.stop()

    def test_returns_float(self):
        f = _make_features()
        score = predict_score(f)
        assert isinstance(score, float)

    def test_fallback_weights_sum_to_one(self):
        # All features = 1.0 → score should be 1.0 (weights sum to 1.0)
        f = np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        score = predict_score(f)
        assert score == pytest.approx(1.0, abs=1e-5)

    def test_fallback_all_zeros_gives_zero(self):
        f = np.zeros(5, dtype=np.float32)
        score = predict_score(f)
        assert score == pytest.approx(0.0)

    def test_popularity_has_highest_weight(self):
        # Only popularity=1, rest=0 → 0.40
        f_pop = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        # Only rating=1, rest=0 → 0.30
        f_rat = np.array([0.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        assert predict_score(f_pop) > predict_score(f_rat)

    def test_fallback_formula_is_correct(self):
        features = np.array([0.8, 0.6, 0.4, 0.3, 0.2], dtype=np.float32)
        expected = 0.40 * 0.8 + 0.30 * 0.6 + 0.10 * 0.4 + 0.15 * 0.3 + 0.05 * 0.2
        assert predict_score(features) == pytest.approx(expected, abs=1e-5)

    def test_score_is_higher_for_better_product(self):
        popular = _make_features(popularity=9000, rating=4.8, days_old=5)
        unpopular = _make_features(popularity=10, rating=2.0, days_old=300)
        assert predict_score(popular) > predict_score(unpopular)


class TestPredictScoreWithModel:
    def test_uses_model_when_available(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.75])
        with patch("ml.model._MODEL", mock_model):
            f = _make_features()
            score = predict_score(f)
        assert score == pytest.approx(0.75)
        mock_model.predict.assert_called_once()

    def test_falls_back_when_model_raises(self):
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("model exploded")
        with patch("ml.model._MODEL", mock_model), \
             patch("ml.model.load_model", return_value=None):
            f = _make_features()
            score = predict_score(f)
        # Should return a valid float from the fallback heuristic
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
