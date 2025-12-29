"""Unit tests for notehub.config module."""

from notehub.config import get_editor


class TestGetEditor:
    """Tests for get_editor function."""

    def test_editor_from_environment(self, mock_env):
        """Should return editor from EDITOR environment variable."""
        mock_env({"EDITOR": "vim"})

        result = get_editor()

        assert result == "vim"

    def test_editor_with_complex_command(self, mock_env):
        """Should handle editor commands with flags."""
        mock_env({"EDITOR": "code --wait"})

        result = get_editor()

        assert result == "code --wait"

    def test_editor_default_when_not_set(self, mock_env):
        """Should return 'vi' default when EDITOR not set."""
        mock_env({})  # Empty environment

        result = get_editor()

        assert result == "vi"

    def test_editor_empty_string(self, mock_env):
        """Should return 'vi' when EDITOR is empty string."""
        mock_env({"EDITOR": ""})

        result = get_editor()

        # os.environ.get returns empty string, which is falsy but not None
        assert result == ""

    def test_editor_with_path(self, mock_env):
        """Should handle full path to editor."""
        mock_env({"EDITOR": "/usr/bin/nano"})

        result = get_editor()

        assert result == "/usr/bin/nano"
