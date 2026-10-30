"""
Visual embedding module using a pretrained CLIP model.

Uses ``openai/clip-vit-base-patch32`` (via ``transformers`` + ``torch``)
to produce 512-dimensional image embeddings.  The model and processor are
loaded lazily on first use — importing this module does **not** download
anything.

All embeddings are L2-normalised, enabling direct cosine similarity /
rank-candidates retrieval.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

# torch is imported lazily inside _load_model() to avoid requiring it at
# import time when the module is merely inspected; however we also re-export
# it here so tests and downstream code can call .to(device), etc. without
# additional imports.  The import is guarded because some CI envs lack torch.
try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

_PathLike = Union[str, Path]


# ── module-level state (lazy-loaded) ────────────────────────────────────────

_MODEL_NAME = "openai/clip-vit-base-patch32"
_state = {"model": None, "processor": None, "device": None, "embedding_dim": None}


def _load_model(device: Optional[str] = None) -> None:
    """Load the CLIP model and processor on first call."""
    if _state["model"] is not None:
        return
    if torch is None:
        raise ImportError(
            "torch is required for CLIP-based embedding extraction. "
            "Install it with: pip install torch --index-url "
            "https://download.pytorch.org/whl/cpu"
        )
    import gc
    from transformers import CLIPVisionModelWithProjection, AutoModel, AutoProcessor, AutoConfig

    # Determine device
    if device is None:
        dev = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        dev = device
    _state["device"] = dev

    processor = AutoProcessor.from_pretrained(_MODEL_NAME)
    model = AutoModel.from_pretrained(_MODEL_NAME).to(dev).eval()

    # Freeze all parameters (no training intended)
    for param in model.parameters():
        param.requires_grad = False

    # Get embedding dimension from config (only fetched when model loads)
    cfg = AutoConfig.from_pretrained(_MODEL_NAME)
    _state["embedding_dim"] = int(cfg.projection_dim)

    _state["model"] = model
    _state["processor"] = processor


# ── public API ───────────────────────────────────────────────────────────────

class VisualEmbeddingExtractor:
    """
    Extract CLIP image embeddings from images.

    Attributes
    ----------
    embedding_dim : int
        Dimensionality of the output vector (512 for clip-vit-base-patch32).

    Examples
    --------
    >>> extractor = VisualEmbeddingExtractor()
    >>> emb = extractor.extract("photo.jpg")       # np.ndarray, shape (512,)
    >>> stack = extractor.extract_batch(["a.jpg", "b.jpg"])  # (2, 512)
    """

    def __init__(self, device: Optional[str] = None) -> None:
        """
        Initialize the extractor.

        Parameters
        ----------
        device : str, optional
            Device to run the model on ("cuda" or "cpu"). If not provided,
            CUDA is used when available, otherwise CPU.
        """
        self._device = device
        self.embedding_dim = _state["embedding_dim"]  # None until first load

    def extract(self, image_path: _PathLike) -> np.ndarray:
        """
        Extract a visual embedding for a single image.

        Parameters
        ----------
        image_path : str or Path
            Path to the input image.

        Returns
        -------
        np.ndarray
            L2-normalised CLIP embedding vector (length ``embedding_dim``).

        Raises
        ------
        FileNotFoundError
            If *image_path* does not exist.
        ValueError
            If the image cannot be opened or processed.
        """
        p = Path(image_path)
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            pil_img = Image.open(p).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Cannot open image {image_path}: {exc}") from exc

        _load_model(device=self._device)
        inputs = _state["processor"](images=pil_img, return_tensors="pt")
        with torch.no_grad():
            outputs = _state["model"].get_image_features(
                **inputs.to(_state["device"])
            )
        # handle newer transformers returning BaseModelOutputWithPooling
        if hasattr(outputs, "pooler_output"):
            feat = outputs.pooler_output
        elif hasattr(outputs, "last_hidden_state"):
            feat = outputs.last_hidden_state[:, 0]
        else:
            feat = outputs
        emb = feat.squeeze(0).cpu().numpy()

        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb

    def extract_batch(
        self,
        image_paths: Iterable[_PathLike],
        *,
        progress_cb: Optional[callable] = None,
    ) -> np.ndarray:
        """
        Extract embeddings for multiple images.

        Parameters
        ----------
        image_paths : iterable of str or Path
            Paths to input images.
        progress_cb : callable(int, int), optional
            Invoked as ``progress_cb(index, total)`` after each image.

        Returns
        -------
        np.ndarray
            Stack of embeddings, shape ``(n_valid, embedding_dim)``.
            Invalid/missing paths are skipped with a warning.
        """
        paths = list(image_paths)
        embeddings: List[np.ndarray] = []
        total = len(paths)

        for idx, path in enumerate(paths):
            try:
                emb = self.extract(path)
                embeddings.append(emb)
            except (FileNotFoundError, ValueError) as exc:
                print(f"[visual_embedding] warning: {exc}")
            if progress_cb is not None:
                progress_cb(idx + 1, total)

        if not embeddings:
            # embedding_dim may be None if the model has not been loaded yet
            return np.empty((0, self.embedding_dim or 0), dtype=np.float64)
        return np.array(embeddings, dtype=np.float64)


def cosine_similarity(feature_a: np.ndarray, feature_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two normalised feature vectors.

    Returns 0.0 when either vector is zero-length.
    Raises ``ValueError`` for mismatched dimensions or empty vectors.
    """
    fa = np.asarray(feature_a, dtype=np.float64).ravel()
    fb = np.asarray(feature_b, dtype=np.float64).ravel()

    if fa.size != fb.size:
        raise ValueError(f"Feature dimension mismatch: {fa.size} vs {fb.size}")
    if fa.size == 0:
        raise ValueError("Feature vectors cannot be empty")

    norm_a = np.linalg.norm(fa)
    norm_b = np.linalg.norm(fb)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(fa, fb) / (norm_a * norm_b))


def rank_candidates(
    query_image: _PathLike,
    candidate_images: Iterable[_PathLike],
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Rank candidate images by cosine similarity to the query image.

    Returns a list of ``(image_path, similarity_score)`` tuples sorted
    descending.  Raises ``FileNotFoundError`` for a missing query and
    ``ValueError`` if any candidate cannot be processed.
    """
    extractor = VisualEmbeddingExtractor()
    query_emb = extractor.extract(query_image)

    scored: List[Tuple[str, float]] = []
    for cand in candidate_images:
        try:
            cand_emb = extractor.extract(cand)
            score = cosine_similarity(query_emb, cand_emb)
            scored.append((str(cand), score))
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(f"Error processing candidate {cand}: {exc}") from exc

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
