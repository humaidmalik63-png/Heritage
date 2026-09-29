"""
Minimal classical image retrieval baseline using color histograms.

Provides:
- extract_features(image_path): Extract normalized RGB color histogram
- cosine_similarity(feature_a, feature_b): Compute cosine similarity
- rank_candidates(query_image, candidate_images, top_k=5): Rank candidates
"""

import numpy as np
from PIL import Image
from pathlib import Path


def extract_features(image_path):
    """
    Extract a normalized RGB color histogram feature from an image.
    
    Args:
        image_path: Path to the image file (str or Path)
        
    Returns:
        numpy.ndarray: Normalized feature vector (dtype=float64)
        
    Raises:
        FileNotFoundError: If image_path does not exist
        ValueError: If image cannot be opened or is invalid
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    try:
        img = Image.open(path)
        img = img.convert('RGB')
        img = img.resize((128, 128))
    except Exception as e:
        raise ValueError(f"Cannot open image {image_path}: {e}")
    
    arr = np.array(img)
    
    # Compute histograms for each channel
    r_hist, _ = np.histogram(arr[:, :, 0], bins=32, range=(0, 255))
    g_hist, _ = np.histogram(arr[:, :, 1], bins=32, range=(0, 255))
    b_hist, _ = np.histogram(arr[:, :, 2], bins=32, range=(0, 255))
    
    # Concatenate and normalize
    feature = np.concatenate([r_hist, g_hist, b_hist]).astype(np.float64)
    
    norm = np.linalg.norm(feature)
    if norm > 0:
        feature = feature / norm
    
    return feature


def cosine_similarity(feature_a, feature_b):
    """
    Compute cosine similarity between two feature vectors.
    
    Args:
        feature_a: First feature vector (numpy.ndarray)
        feature_b: Second feature vector (numpy.ndarray)
        
    Returns:
        float: Cosine similarity score (range: -1 to 1, but typically 0-1 for histograms)
        
    Raises:
        ValueError: If feature vectors have different dimensions or are zero-length
    """
    if len(feature_a) != len(feature_b):
        raise ValueError(f"Feature dimension mismatch: {len(feature_a)} vs {len(feature_b)}")
    
    if len(feature_a) == 0:
        raise ValueError("Feature vectors cannot be empty")
    
    dot_product = np.dot(feature_a, feature_b)
    norm_a = np.linalg.norm(feature_a)
    norm_b = np.linalg.norm(feature_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))


def rank_candidates(query_image, candidate_images, top_k=5):
    """
    Rank candidate images by similarity to the query image.
    
    Args:
        query_image: Path to the query image (str or Path)
        candidate_images: List of paths to candidate images
        top_k: Number of top results to return (default: 5)
        
    Returns:
        list of tuples: [(image_path, similarity_score), ...] sorted by score descending
        
    Raises:
        FileNotFoundError: If query_image or any candidate does not exist
        ValueError: If images cannot be processed
    """
    # Extract query features
    query_features = extract_features(query_image)
    
    # Score each candidate
    scored_candidates = []
    for candidate_path in candidate_images:
        try:
            candidate_features = extract_features(candidate_path)
            score = cosine_similarity(query_features, candidate_features)
            scored_candidates.append((str(candidate_path), score))
        except (FileNotFoundError, ValueError) as e:
            # Re-raise with context
            raise ValueError(f"Error processing candidate {candidate_path}: {e}")
    
    # Sort by similarity descending
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Return top-k
    return scored_candidates[:top_k]
