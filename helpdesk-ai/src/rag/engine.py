"""Retrieval-augmented generation engine placeholder."""


def build_index(documents: list[str]) -> dict:
    """Build a minimal in-memory index."""
    return {"documents": documents}


def query(index: dict, text: str) -> dict:
    """Return a minimal retrieval result."""
    return {"query": text, "documents": index.get("documents", [])}
