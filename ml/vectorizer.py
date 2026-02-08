from typing import Iterable, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix


def build_vectorizer(
    texts: Iterable[str],
    *,
    max_features: int = 5000,
    ngram_range: tuple = (1, 2),
) -> Tuple[TfidfVectorizer, csr_matrix]:
    """
    Build and fit a TF-IDF vectorizer.

    Returns:
        vectorizer: fitted TfidfVectorizer
        matrix: TF-IDF feature matrix
    """
    if not texts:
        raise ValueError("Input texts must be a non-empty iterable of strings")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=ngram_range,
        max_features=max_features,
        dtype=float,
    )

    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix
