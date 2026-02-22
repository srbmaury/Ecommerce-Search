import hashlib


def normalize_query(query: str) -> str:
    return " ".join((query or "").strip().lower().split())


def query_hash(query: str) -> str:
    normalized_query = normalize_query(query)
    return hashlib.sha1(normalized_query.encode("utf-8")).hexdigest()[:16]
