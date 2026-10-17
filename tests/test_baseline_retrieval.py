"""
Tests for baseline retrieval module.

Uses synthetic test images to validate the functionality of
ml/baseline_retrieval.py.
"""

import unittest
import tempfile
import os
from pathlib import Path
import numpy as np
from PIL import Image

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.baseline_retrieval import extract_features, cosine_similarity, rank_candidates


class TestExtractFeatures(unittest.TestCase):
    """Test cases for extract_features function."""
    
    def setUp(self):
        """Set up test environment with synthetic images."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a simple test image
        self.test_image_path = Path(self.temp_dir) / "test_image.jpg"
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        img.save(self.test_image_path)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_extract_features_returns_array(self):
        """Test that extract_features returns a numpy array."""
        features = extract_features(self.test_image_path)
        self.assertIsInstance(features, np.ndarray)
    
    def test_extract_features_correct_dimension(self):
        """Test that feature vector has expected dimension (96 = 32 bins * 3 channels)."""
        features = extract_features(self.test_image_path)
        self.assertEqual(len(features), 96)
    
    def test_extract_features_normalized(self):
        """Test that feature vector is L2-normalized."""
        features = extract_features(self.test_image_path)
        norm = np.linalg.norm(features)
        self.assertAlmostEqual(norm, 1.0, places=6)
    
    def test_extract_features_non_negative(self):
        """Test that feature values are non-negative (histogram counts)."""
        features = extract_features(self.test_image_path)
        self.assertTrue(np.all(features >= 0))
    
    def test_extract_features_missing_file(self):
        """Test that FileNotFoundError is raised for missing image."""
        with self.assertRaises(FileNotFoundError):
            extract_features("nonexistent_image.jpg")
    
    def test_extract_features_invalid_path_type(self):
        """Test that appropriate error is raised for invalid path."""
        with self.assertRaises((FileNotFoundError, ValueError, TypeError)):
            extract_features(12345)  # Invalid path type


class TestCosineSimilarity(unittest.TestCase):
    """Test cases for cosine_similarity function."""
    
    def test_cosine_similarity_identical_vectors(self):
        """Test that identical vectors have similarity 1.0."""
        vec = np.array([1.0, 0.0, 0.0])
        similarity = cosine_similarity(vec, vec)
        self.assertAlmostEqual(similarity, 1.0, places=6)
    
    def test_cosine_similarity_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity 0.0."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0, places=6)
    
    def test_cosine_similarity_opposite_vectors(self):
        """Test that opposite vectors have similarity -1.0."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, -1.0, places=6)
    
    def test_cosine_similarity_zero_vector(self):
        """Test that zero vector returns 0.0 similarity."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 0.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)
        self.assertEqual(similarity, 0.0)
    
    def test_cosine_similarity_dimension_mismatch(self):
        """Test that ValueError is raised for mismatched dimensions."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        with self.assertRaises(ValueError):
            cosine_similarity(vec1, vec2)
    
    def test_cosine_similarity_empty_vectors(self):
        """Test that ValueError is raised for empty vectors."""
        vec1 = np.array([])
        vec2 = np.array([])
        with self.assertRaises(ValueError):
            cosine_similarity(vec1, vec2)


class TestRankCandidates(unittest.TestCase):
    """Test cases for rank_candidates function."""
    
    def setUp(self):
        """Set up test environment with synthetic images."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test images with different colors
        self.red_image = Path(self.temp_dir) / "red.jpg"
        self.blue_image = Path(self.temp_dir) / "blue.jpg"
        self.green_image = Path(self.temp_dir) / "green.jpg"
        
        Image.new('RGB', (100, 100), (255, 0, 0)).save(self.red_image)
        Image.new('RGB', (100, 100), (0, 0, 255)).save(self.blue_image)
        Image.new('RGB', (100, 100), (0, 255, 0)).save(self.green_image)
        
        # Create query image (similar to red but slightly different)
        self.query_image = Path(self.temp_dir) / "query.jpg"
        Image.new('RGB', (100, 100), (200, 50, 50)).save(self.query_image)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_rank_candidates_returns_list(self):
        """Test that rank_candidates returns a list."""
        candidates = [str(self.red_image), str(self.blue_image), str(self.green_image)]
        results = rank_candidates(str(self.query_image), candidates, top_k=2)
        self.assertIsInstance(results, list)
    
    def test_rank_candidates_returns_correct_number(self):
        """Test that rank_candidates returns exactly top_k results."""
        candidates = [str(self.red_image), str(self.blue_image), str(self.green_image)]
        results = rank_candidates(str(self.query_image), candidates, top_k=2)
        self.assertEqual(len(results), 2)
    
    def test_rank_candidates_sorted_by_similarity(self):
        """Test that results are sorted by similarity in descending order."""
        candidates = [str(self.red_image), str(self.blue_image), str(self.green_image)]
        results = rank_candidates(str(self.query_image), candidates, top_k=3)
        
        scores = [score for _, score in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_rank_candidates_returns_tuples(self):
        """Test that each result is a tuple of (path, score)."""
        candidates = [str(self.red_image), str(self.blue_image), str(self.green_image)]
        results = rank_candidates(str(self.query_image), candidates, top_k=2)
        
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], str)
            self.assertIsInstance(result[1], float)
    
    def test_rank_candidates_similarity_range(self):
        """Test that similarity scores are within valid range."""
        candidates = [str(self.red_image), str(self.blue_image), str(self.green_image)]
        results = rank_candidates(str(self.query_image), candidates, top_k=3)
        
        for _, score in results:
            self.assertGreaterEqual(score, -1.0)
            self.assertLessEqual(score, 1.0)
    
    def test_rank_candidates_missing_query(self):
        """Test that FileNotFoundError is raised for missing query image."""
        candidates = [str(self.red_image)]
        with self.assertRaises(FileNotFoundError):
            rank_candidates("nonexistent_query.jpg", candidates)
    
    def test_rank_candidates_missing_candidate(self):
        """Test that ValueError is raised for missing candidate image."""
        candidates = [str(self.red_image), "nonexistent_candidate.jpg"]
        with self.assertRaises(ValueError):
            rank_candidates(str(self.query_image), candidates)
    
    def test_rank_candidates_empty_candidates(self):
        """Test that empty candidate list returns empty results."""
        results = rank_candidates(str(self.query_image), [], top_k=5)
        self.assertEqual(results, [])
    
    def test_rank_candidates_top_k_larger_than_candidates(self):
        """Test that top_k larger than candidate count returns all candidates."""
        candidates = [str(self.red_image), str(self.blue_image)]
        results = rank_candidates(str(self.query_image), candidates, top_k=10)
        self.assertEqual(len(results), 2)


class TestInvalidImageHandling(unittest.TestCase):
    """Verify invalid/corrupt images and empty retrieval are handled safely."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.valid_image = Path(self.temp_dir) / "valid.jpg"
        Image.new('RGB', (100, 100), (255, 0, 0)).save(self.valid_image)
        self.corrupt_image = Path(self.temp_dir) / "corrupt.jpg"
        self.corrupt_image.write_text("not an image")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_extract_features_invalid_image_raises(self):
        with self.assertRaises(ValueError):
            extract_features(self.corrupt_image)

    def test_rank_candidates_invalid_candidate_raises(self):
        with self.assertRaises(ValueError):
            rank_candidates(str(self.valid_image), [str(self.corrupt_image)])

    def test_rank_candidates_empty_candidates(self):
        results = rank_candidates(str(self.valid_image), [], top_k=5)
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
