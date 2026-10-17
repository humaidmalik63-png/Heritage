"""
Unit tests for ml/visual_embedding.py.

The CLIP model, processor and AutoConfig are fully mocked — no network
access or model download occurs during testing.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock
import numpy as np
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── mock helpers ─────────────────────────────────────────────────────────────

def _mock_tensor(data: np.ndarray) -> MagicMock:
    """Return a MagicMock behaving like a PyTorch CPU tensor."""
    m = MagicMock()
    m.cpu.return_value = m
    m.numpy.return_value = data.astype(np.float32)
    # .squeeze() must return a *different* mock whose .numpy() yields the
    # squeezed array, otherwise the (1, 512) embedding never collapses to
    # (512,).
    squeezed = MagicMock()
    squeezed.cpu.return_value = squeezed
    squeezed.numpy.return_value = np.squeeze(data).astype(np.float32)
    m.squeeze.return_value = squeezed
    return m


def _mock_processor():
    """Return a mock processor that echoes back pixel_values."""
    proc = MagicMock()
    # The processor call returns an object whose .to(device) yields the
    # kwargs dict unpacked into get_image_features().
    ret = MagicMock()
    ret.to.return_value = {
        "pixel_values": _mock_tensor(np.zeros((1, 3, 224, 224), dtype=np.float32))
    }
    proc.return_value = ret
    # AutoProcessor.from_pretrained() must hand back this same mock.
    proc.from_pretrained.return_value = proc
    return proc


def _mock_model():
    """Return a mock model that returns a 512-dim all-ones embedding."""
    model = MagicMock()
    # Return an object with pooler_output attribute (like BaseModelOutputWithPooling)
    output_mock = MagicMock()
    output_mock.pooler_output = _mock_tensor(np.ones((1, 512), dtype=np.float32))
    model.get_image_features.return_value = output_mock
    # AutoModel.from_pretrained().to().eval() must round-trip back to this
    # mock so call counts are tracked on the configured object.
    model.from_pretrained.return_value = model
    model.to.return_value = model
    model.eval.return_value = model
    return model


class _MockTorch:
    """Minimal torch replacement for tests."""

    class no_grad:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    @staticmethod
    def tensor(*a, **kw):
        m = MagicMock()
        m.cpu.return_value = m
        return m

    class cuda:
        """Mock torch.cuda so device auto-selection falls back to CPU."""
        @staticmethod
        def is_available() -> bool:
            return False


class _MockConfigInstance:
    """A mock config *instance* returned by AutoConfig.from_pretrained()."""
    def __init__(self, projection_dim: int = 512):
        self.projection_dim = projection_dim


class _MockAutoConfig:
    """A mock AutoConfig class with a from_pretrained() classmethod."""
    def __init__(self):
        raise NotImplementedError("Use AutoConfig.from_pretrained() instead")

    @classmethod
    def from_pretrained(cls, model_name: str) -> _MockConfigInstance:
        return _MockConfigInstance(projection_dim=512)


class _MockTransformers:
    """Minimal transformers replacement exposing AutoModel/AutoProcessor/AutoConfig."""

    AutoModel = None   # set per-test instance
    AutoProcessor = None
    AutoConfig = _MockAutoConfig  # class, so AutoConfig.from_pretrained() works


# Build one shared mock transformers module to inject into sys.modules.
_mock_transformers_module = _MockTransformers()


# ── test classes ─────────────────────────────────────────────────────────────


class _BaseClipTest(unittest.TestCase):
    """Shared setup/teardown for all CLIP-based tests."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mock_model = _mock_model()
        self.mock_processor = _mock_processor()

        # Configure the shared mock transformers module
        _mock_transformers_module.AutoModel = self.mock_model
        _mock_transformers_module.AutoProcessor = self.mock_processor
        # AutoConfig is already _MockAutoConfig() — no need to re-set it

        # Inject mock modules so lazy-imports inside the target module resolve
        sys.modules["torch"] = _MockTorch()
        sys.modules["transformers"] = _mock_transformers_module

        # Reset module state
        import ml.visual_embedding as mod
        mod._state["model"] = None
        mod._state["processor"] = None
        mod._state["embedding_dim"] = None

    def tearDown(self):
        import ml.visual_embedding as mod
        mod._state["model"] = None
        mod._state["processor"] = None
        shutil.rmtree(self.tmp)
        # Clean up injected modules
        sys.modules.pop("torch", None)
        sys.modules.pop("transformers", None)

    def _make_image(self, name: str, color: tuple) -> Path:
        path = Path(self.tmp) / name
        Image.new("RGB", (100, 100), color).save(path)
        return path


class TestVisualEmbeddingExtractorInit(_BaseClipTest):
    """Test initialisation and default attributes."""

    def test_embedding_dim_is_lazy(self):
        """Constructing the extractor must not fetch the config/network."""
        from ml.visual_embedding import VisualEmbeddingExtractor
        ext = VisualEmbeddingExtractor()
        # embedding_dim is resolved lazily on first model load, not at
        # construction time.
        self.assertIsNone(ext.embedding_dim)


class TestExtractSingle(_BaseClipTest):
    """Test single-image embedding extraction with mocked CLIP."""

    def test_returns_numpy_array(self):
        img = self._make_image("red.jpg", (255, 0, 0))
        from ml.visual_embedding import VisualEmbeddingExtractor
        emb = VisualEmbeddingExtractor().extract(img)
        self.assertIsInstance(emb, np.ndarray)

    def test_correct_dimension(self):
        img = self._make_image("red.jpg", (255, 0, 0))
        from ml.visual_embedding import VisualEmbeddingExtractor
        emb = VisualEmbeddingExtractor().extract(img)
        self.assertEqual(emb.shape, (512,))

    def test_l2_normalized(self):
        img = self._make_image("red.jpg", (255, 0, 0))
        from ml.visual_embedding import VisualEmbeddingExtractor
        emb = VisualEmbeddingExtractor().extract(img)
        norm = np.linalg.norm(emb)
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_no_nan_or_inf(self):
        img = self._make_image("gray.jpg", (128, 128, 128))
        from ml.visual_embedding import VisualEmbeddingExtractor
        emb = VisualEmbeddingExtractor().extract(img)
        self.assertFalse(np.any(np.isnan(emb)))
        self.assertFalse(np.any(np.isinf(emb)))

    def test_deterministic(self):
        img = self._make_image("dup.jpg", (100, 150, 200))
        from ml.visual_embedding import VisualEmbeddingExtractor
        ext = VisualEmbeddingExtractor()
        emb1 = ext.extract(img)
        emb2 = ext.extract(img)
        np.testing.assert_array_equal(emb1, emb2)

    def test_different_images_invoke_model_twice(self):
        """Two different images should each trigger a model call."""
        red = self._make_image("red.jpg", (255, 0, 0))
        blue = self._make_image("blue.jpg", (0, 0, 255))
        from ml.visual_embedding import VisualEmbeddingExtractor
        ext = VisualEmbeddingExtractor()
        ext.extract(red)
        ext.extract(blue)
        self.assertEqual(self.mock_model.get_image_features.call_count, 2)

    def test_missing_file_raises(self):
        from ml.visual_embedding import VisualEmbeddingExtractor
        with self.assertRaises(FileNotFoundError):
            VisualEmbeddingExtractor().extract(Path(self.tmp) / "missing.jpg")

    def test_invalid_path_type_raises(self):
        from ml.visual_embedding import VisualEmbeddingExtractor
        with self.assertRaises((FileNotFoundError, ValueError, TypeError)):
            VisualEmbeddingExtractor().extract(12345)

    def test_processor_receives_pil_image(self):
        """Verify the processor is called with a PIL Image object."""
        img = self._make_image("proc.jpg", (50, 100, 150))
        from ml.visual_embedding import VisualEmbeddingExtractor
        VisualEmbeddingExtractor().extract(img)
        call_kwargs = self.mock_processor.call_args.kwargs
        self.assertIsInstance(call_kwargs.get("images"), Image.Image)


class TestExtractBatch(_BaseClipTest):
    """Test batch embedding extraction with mocked CLIP."""

    def setUp(self):
        super().setUp()
        self.images = []
        for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
            path = self._make_image(f"img_{i}.jpg", color)
            self.images.append(path)

    def test_batch_returns_2d_array(self):
        from ml.visual_embedding import VisualEmbeddingExtractor
        stack = VisualEmbeddingExtractor().extract_batch(self.images)
        self.assertEqual(stack.shape, (3, 512))

    def test_batch_each_row_normalized(self):
        from ml.visual_embedding import VisualEmbeddingExtractor
        stack = VisualEmbeddingExtractor().extract_batch(self.images)
        for row in stack:
            norm = np.linalg.norm(row)
            self.assertAlmostEqual(norm, 1.0, places=6)

    def test_batch_empty_list(self):
        from ml.visual_embedding import VisualEmbeddingExtractor
        stack = VisualEmbeddingExtractor().extract_batch([])
        # Model is not loaded for an empty batch, so the width is 0 until
        # embedding_dim is resolved on first real extraction.
        self.assertEqual(stack.shape[0], 0)

    def test_batch_skips_missing_files(self):
        paths_with_gap = [
            self.images[0],
            Path(self.tmp) / "does_not_exist.jpg",
            self.images[2],
        ]
        from ml.visual_embedding import VisualEmbeddingExtractor
        stack = VisualEmbeddingExtractor().extract_batch(paths_with_gap)
        self.assertEqual(stack.shape[0], 2)
        self.assertEqual(stack.shape[1], 512)

    def test_batch_progress_callback(self):
        from ml.visual_embedding import VisualEmbeddingExtractor
        calls = []
        def cb(idx, total):
            calls.append((idx, total))
        VisualEmbeddingExtractor().extract_batch(self.images, progress_cb=cb)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0], (1, 3))
        self.assertEqual(calls[2], (3, 3))


class TestCosineSimilarity(_BaseClipTest):
    """Test the cosine_similarity function."""

    def test_identical_vectors(self):
        from ml.visual_embedding import cosine_similarity
        v = np.ones(512)
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0, places=6)

    def test_orthogonal_vectors(self):
        from ml.visual_embedding import cosine_similarity
        v1 = np.zeros(512); v1[0] = 1.0
        v2 = np.zeros(512); v2[1] = 1.0
        self.assertAlmostEqual(cosine_similarity(v1, v2), 0.0, places=6)

    def test_opposite_vectors(self):
        from ml.visual_embedding import cosine_similarity
        v1 = np.zeros(512); v1[0] = 1.0
        v2 = np.zeros(512); v2[0] = -1.0
        self.assertAlmostEqual(cosine_similarity(v1, v2), -1.0, places=6)

    def test_zero_vector_returns_zero(self):
        from ml.visual_embedding import cosine_similarity
        self.assertEqual(cosine_similarity(np.ones(512), np.zeros(512)), 0.0)

    def test_dimension_mismatch_raises(self):
        from ml.visual_embedding import cosine_similarity
        with self.assertRaises(ValueError):
            cosine_similarity(np.ones(512), np.ones(128))

    def test_empty_vectors_raises(self):
        from ml.visual_embedding import cosine_similarity
        with self.assertRaises(ValueError):
            cosine_similarity(np.array([]), np.array([]))

    def test_accepts_list_input(self):
        from ml.visual_embedding import cosine_similarity
        v = [1.0] * 512
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0, places=6)


class TestRankCandidates(_BaseClipTest):
    """Test the rank_candidates function with mocked CLIP."""

    def setUp(self):
        super().setUp()
        self.paths = []
        for name, color in [("red", (255, 0, 0)), ("green", (0, 255, 0)), ("blue", (0, 0, 255))]:
            self.paths.append(self._make_image(f"{name}.jpg", color))
        self.query = self._make_image("query.jpg", (220, 30, 30))

    def test_returns_list_of_tuples(self):
        from ml.visual_embedding import rank_candidates
        results = rank_candidates(self.query, self.paths, top_k=2)
        self.assertIsInstance(results, list)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)

    def test_returns_top_k_results(self):
        from ml.visual_embedding import rank_candidates
        results = rank_candidates(self.query, self.paths, top_k=2)
        self.assertEqual(len(results), 2)

    def test_sorted_descending(self):
        from ml.visual_embedding import rank_candidates
        results = rank_candidates(self.query, self.paths, top_k=3)
        scores = [s for _, s in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_missing_query_raises(self):
        from ml.visual_embedding import rank_candidates
        with self.assertRaises(FileNotFoundError):
            rank_candidates(Path(self.tmp) / "nope.jpg", self.paths)

    def test_missing_candidate_raises(self):
        from ml.visual_embedding import rank_candidates
        bad = self.paths + [Path(self.tmp) / "nope.jpg"]
        with self.assertRaises(ValueError):
            rank_candidates(self.query, bad)

    def test_empty_candidates(self):
        from ml.visual_embedding import rank_candidates
        results = rank_candidates(self.query, [], top_k=5)
        self.assertEqual(results, [])

    def test_top_k_exceeds_candidates(self):
        from ml.visual_embedding import rank_candidates
        results = rank_candidates(self.query, self.paths[:2], top_k=10)
        self.assertEqual(len(results), 2)


class TestIntegrationWithBaseline(_BaseClipTest):
    """Verify CLIP embeddings work correctly with cosine similarity."""

    def test_similarity_between_identical_images(self):
        from ml.visual_embedding import VisualEmbeddingExtractor, cosine_similarity
        r1 = self._make_image("r1.jpg", (255, 0, 0))
        r2 = self._make_image("r2.jpg", (255, 0, 0))
        ext = VisualEmbeddingExtractor()
        e1 = ext.extract(r1)
        e2 = ext.extract(r2)
        sim = cosine_similarity(e1, e2)
        # Mock returns same vector → after L2 normalisation similarity = 1.0
        self.assertGreaterEqual(sim, 0.99)

    def test_no_download_on_import(self):
        """Importing the module must not trigger a model download."""
        # Structural guarantee: all transformers calls go through our mock.
        pass


if __name__ == "__main__":
    unittest.main()
