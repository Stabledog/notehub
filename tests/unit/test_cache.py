"""Unit tests for notehub.cache module."""

from pathlib import Path

from notehub import cache


class TestCacheDiscovery:
    """Tests for cache discovery functions."""

    def test_find_all_cached_notes_empty_cache(self, mocker):
        """Should return empty list when cache directory doesn't exist."""
        mocker.patch("notehub.cache.get_cache_root", return_value=Path("/nonexistent"))

        result = cache.find_all_cached_notes()

        assert result == []

    def test_find_all_cached_notes_multiple_repos(self, mocker, tmp_path):
        """Should find all cached notes across multiple repos."""
        # Create mock cache structure
        cache_root = tmp_path / "cache"
        cache_root.mkdir()

        # Create cache directories with .git
        cache1 = cache_root / "github.com" / "org1" / "repo1" / "1"
        cache1.mkdir(parents=True)
        (cache1 / ".git").mkdir()

        cache2 = cache_root / "github.com" / "org1" / "repo1" / "2"
        cache2.mkdir(parents=True)
        (cache2 / ".git").mkdir()

        cache3 = cache_root / "github.com" / "org2" / "repo2" / "5"
        cache3.mkdir(parents=True)
        (cache3 / ".git").mkdir()

        mocker.patch("notehub.cache.get_cache_root", return_value=cache_root)

        result = cache.find_all_cached_notes()

        assert len(result) == 3
        assert ("github.com", "org1", "repo1", 1, cache1) in result
        assert ("github.com", "org1", "repo1", 2, cache2) in result
        assert ("github.com", "org2", "repo2", 5, cache3) in result

    def test_find_all_cached_notes_skips_non_git_dirs(self, mocker, tmp_path):
        """Should skip directories without .git subdirectory."""
        cache_root = tmp_path / "cache"
        cache_root.mkdir()

        # Create valid cache
        valid_cache = cache_root / "github.com" / "org" / "repo" / "1"
        valid_cache.mkdir(parents=True)
        (valid_cache / ".git").mkdir()

        # Create invalid cache (no .git)
        invalid_cache = cache_root / "github.com" / "org" / "repo" / "2"
        invalid_cache.mkdir(parents=True)

        mocker.patch("notehub.cache.get_cache_root", return_value=cache_root)

        result = cache.find_all_cached_notes()

        assert len(result) == 1
        assert result[0][3] == 1  # Only issue 1

    def test_find_all_cached_notes_skips_non_numeric_dirs(self, mocker, tmp_path):
        """Should skip directories with non-numeric names."""
        cache_root = tmp_path / "cache"
        cache_root.mkdir()

        # Create valid cache
        valid_cache = cache_root / "github.com" / "org" / "repo" / "123"
        valid_cache.mkdir(parents=True)
        (valid_cache / ".git").mkdir()

        # Create invalid cache (non-numeric)
        invalid_cache = cache_root / "github.com" / "org" / "repo" / "abc"
        invalid_cache.mkdir(parents=True)
        (invalid_cache / ".git").mkdir()

        mocker.patch("notehub.cache.get_cache_root", return_value=cache_root)

        result = cache.find_all_cached_notes()

        assert len(result) == 1
        assert result[0][3] == 123

    def test_find_dirty_cached_notes(self, mocker, tmp_path):
        """Should filter for dirty notes only."""
        cache_root = tmp_path / "cache"

        # Create mock caches
        cache1 = cache_root / "github.com" / "org" / "repo" / "1"
        cache2 = cache_root / "github.com" / "org" / "repo" / "2"

        all_notes = [
            ("github.com", "org", "repo", 1, cache1),
            ("github.com", "org", "repo", 2, cache2),
        ]
        mocker.patch("notehub.cache.find_all_cached_notes", return_value=all_notes)

        # Mock is_dirty to return True for first note only
        def mock_is_dirty(path):
            return path == cache1

        mocker.patch("notehub.cache.is_dirty", side_effect=mock_is_dirty)

        result = cache.find_dirty_cached_notes()

        assert len(result) == 1
        assert result[0][3] == 1  # Only issue 1 is dirty

    def test_find_dirty_cached_notes_none_dirty(self, mocker):
        """Should return empty list when no notes are dirty."""
        all_notes = [
            ("github.com", "org", "repo", 1, Path("/cache/1")),
        ]
        mocker.patch("notehub.cache.find_all_cached_notes", return_value=all_notes)
        mocker.patch("notehub.cache.is_dirty", return_value=False)

        result = cache.find_dirty_cached_notes()

        assert result == []

    def test_find_all_cached_notes_enterprise_host(self, mocker, tmp_path):
        """Should handle enterprise GitHub hosts."""
        cache_root = tmp_path / "cache"
        cache_root.mkdir()

        # Create cache with enterprise host
        cache_path = cache_root / "github.example.com" / "org" / "repo" / "42"
        cache_path.mkdir(parents=True)
        (cache_path / ".git").mkdir()

        mocker.patch("notehub.cache.get_cache_root", return_value=cache_root)

        result = cache.find_all_cached_notes()

        assert len(result) == 1
        assert result[0][0] == "github.example.com"
        assert result[0][3] == 42
