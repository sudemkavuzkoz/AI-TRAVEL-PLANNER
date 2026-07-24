import os
import torch
from sentence_transformers import SentenceTransformer

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "model_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

_model = None

def _get_model():
    global _model
    if _model is None:
        print(f"[Embedding] Model yukleniyor: {_MODEL_NAME} (Cihaz: {_DEVICE})")
        _model = SentenceTransformer(_MODEL_NAME, device=_DEVICE, cache_folder=_CACHE_DIR)
        print(f"[Embedding] Model hazir! Cihaz: {_DEVICE.upper()}")
    return _model

def create_embedding(text):
    try:
        return _get_model().encode(text, normalize_embeddings=True).tolist()
    except Exception as e:
        raise Exception(f"Embedding hatasi: {e}")

def create_embeddings(texts):
    if not texts:
        return []
    try:
        vectors = _get_model().encode(
            texts,
            normalize_embeddings=True,
            batch_size=64,
            show_progress_bar=False
        )
        return vectors.tolist()
    except Exception as e:
        raise Exception(f"Toplu embedding hatasi: {e}")