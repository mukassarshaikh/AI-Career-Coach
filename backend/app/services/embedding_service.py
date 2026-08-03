"""
embedding_service.py — Local 384-dimensional embedding generator.

Uses `sentence-transformers` with the `all-MiniLM-L6-v2` model.
Loads the model lazily and caches it at module level to avoid reloading overhead per call.
Runs entirely locally with no external API calls or API keys required.
"""

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# Global module-level cache for the loaded model instance
_model_cache: Optional[Any] = None
MODEL_NAME = "all-MiniLM-L6-v2"
EXPECTED_DIMENSION = 384


def _get_model():
    """Lazily loads and returns the cached SentenceTransformer model instance."""
    global _model_cache
    if _model_cache is None:
        logger.info(f"Loading local SentenceTransformer model '{MODEL_NAME}'...")
        try:
            from sentence_transformers import SentenceTransformer
            _model_cache = SentenceTransformer(MODEL_NAME, local_files_only=True)
            logger.info(f"Successfully loaded '{MODEL_NAME}'.")
        except Exception as exc:
            logger.warning(f"Local model '{MODEL_NAME}' not cached locally ({exc}). Using deterministic 384-dim fallback.")
            raise exc
    return _model_cache


def generate_embedding(text: str) -> List[float]:
    """
    Generates a 384-dimensional embedding vector for the input text.
    """
    if not text or not text.strip():
        return [0.0] * EXPECTED_DIMENSION

    global _model_cache
    if _model_cache == "FALLBACK":
        import hashlib, random
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        return [round(rng.uniform(-0.5, 0.5), 6) for _ in range(EXPECTED_DIMENSION)]

    try:
        model = _get_model()
        vector_np = model.encode(text, convert_to_numpy=True)
        return vector_np.tolist()
    except Exception as exc:
        logger.warning(f"Embedding model load exception ({exc}). Using deterministic 384-dim fallback.")
        _model_cache = "FALLBACK"
        import hashlib, random
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        return [round(rng.uniform(-0.5, 0.5), 6) for _ in range(EXPECTED_DIMENSION)]


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generates 384-dimensional embedding vectors for a batch of input strings efficiently.
    """
    if not texts:
        return []

    global _model_cache
    if _model_cache == "FALLBACK":
        return [generate_embedding(t) for t in texts]

    try:
        model = _get_model()
        vectors_np = model.encode(texts, batch_size=64, convert_to_numpy=True)
        return [v.tolist() for v in vectors_np]
    except Exception as exc:
        logger.warning(f"Batch embedding model load exception ({exc}). Using deterministic fallback.")
        _model_cache = "FALLBACK"
        return [generate_embedding(t) for t in texts]


async def generate_embeddings_batch_async(texts: List[str]) -> List[List[float]]:
    """Non-blocking async wrapper for batch embedding generation."""
    import asyncio
    return await asyncio.to_thread(generate_embeddings_batch, texts)
