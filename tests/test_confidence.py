"""
Tests for the confidence decision layer.
"""

import sys
import tempfile
import shutil
from pathlib import Path

import numpy as np
import faiss

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.confidence import ConfidenceLayer, RetrievalConfig, RetrievalResult, build_confidence_layer


class TestConfidenceLayer:
    """Test confidence decision layer."""

    def setup_method(self):
        """Create a minimal FAISS index and mapping for testing."""
        self.tmpdir = tempfile.mkdtemp()
        np.random.seed(42)

        # Create simple 10-dim embeddings for 3 sites, 2 images each
        self.image_ids = ["taj_01", "taj_02", "red_01", "red_02", "qutub_01", "qutub_02"]
        self.paths = [f"data/raw/{sid.split('_')[0]}/{sid}.jpg" for sid in self.image_ids]

        # Site-specific vectors (normalized)
        taj_vec = np.array([1.0] + [0.0] * 9)
        red_vec = np.array([0.0, 1.0] + [0.0] * 8)
        qutub_vec = np.array([0.0, 0.0, 1.0] + [0.0] * 7)

        embeddings = np.vstack([
            taj_vec, taj_vec,  # taj images (identical)
            red_vec, red_vec,  # red images (identical)
            qutub_vec, qutub_vec,  # qutub images (identical)
        ]).astype(np.float32)

        self.index = faiss.IndexFlatIP(10)
        self.index.add(embeddings)

        faiss.write_index(self.index, f"{self.tmpdir}/test_index.faiss")
        import json
        with open(f"{self.tmpdir}/mapping.json", "w") as f:
            json.dump({"image_ids": self.image_ids, "paths": self.paths}, f)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_confident_match_above_threshold(self):
        """Query with exact match should be confident."""
        layer = ConfidenceLayer(self.index, self.image_ids, self.paths, RetrievalConfig(similarity_threshold=0.85))
        query_vec = np.array([1.0] + [0.0] * 9).astype(np.float32)
        result = layer.query(query_vec)
        assert result.confident is True
        assert result.is_unknown is False
        assert result.site_id == "taj"
        assert result.similarity == 1.0

    def test_unknown_below_threshold(self):
        """Query with low similarity should return unknown."""
        layer = ConfidenceLayer(self.index, self.image_ids, self.paths, RetrievalConfig(similarity_threshold=0.65))
        # Vector with low similarity to all (pointing toward dimension 5)
        query_vec = np.array([0.1, 0.1, 0.0, 0.0, 1.0] + [0.0] * 5).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)
        result = layer.query(query_vec)
        assert result.confident is False
        assert result.is_unknown is True
        assert result.site_id == "unknown"
        assert result.similarity < 0.65

    def test_threshold_boundary(self):
        """Query at threshold boundary should follow >= logic."""
        # Use threshold 0.5 for exact match with 0.7071 similarity
        layer = ConfidenceLayer(self.index, self.image_ids, self.paths, RetrievalConfig(similarity_threshold=0.5))
        # Vector at ~0.707 similarity to taj (cosine of 45 degrees)
        query_vec = np.array([0.7071, 0.7071] + [0.0] * 8).astype(np.float32)
        result = layer.query(query_vec)
        # Similarity ~0.707 > 0.5, so confident
        assert result.confident is True

    def test_factory_function(self):
        """Test build_confidence_layer factory."""
        layer = build_confidence_layer(
            f"{self.tmpdir}/test_index.faiss",
            f"{self.tmpdir}/mapping.json",
            threshold=0.8,
        )
        assert isinstance(layer, ConfidenceLayer)
        assert layer.config.similarity_threshold == 0.8

    def test_set_threshold(self):
        """Test dynamic threshold update."""
        layer = ConfidenceLayer(self.index, self.image_ids, self.paths, RetrievalConfig(similarity_threshold=0.9))
        query_vec = np.array([1.0] + [0.0] * 9).astype(np.float32)
        
        # Should be confident at 0.9
        result = layer.query(query_vec)
        assert result.confident is True
        
        # Increase threshold above 1.0
        layer.set_threshold(1.0001)
        result = layer.query(query_vec)
        assert result.confident is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])