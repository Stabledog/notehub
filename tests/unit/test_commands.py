"""Unit tests for notehub command modules."""

from argparse import Namespace

from notehub.commands import add, edit
from notehub.gh_wrapper import GhError


class TestPrepareEditorCommand:
    """Tests for _prepare_editor_command function."""

    def test_regular_editor(self, mocker):
        """Should return editor as single-item list."""
        mocker.patch("shutil.which", return_value="/usr/bin/vim")
        result = edit._prepare_editor_command("vim")
        assert result == ["/usr/bin/vim"]

    def test_vscode_without_flag(self, mocker):
        """Should add --wait flag for VS Code."""
        mocker.patch("shutil.which", return_value="/usr/local/bin/code")
        result = edit._prepare_editor_command("code")
        assert result == ["/usr/local/bin/code", "--wait"]

    def test_vscode_exe_windows(self, mocker):
        """Should detect code.exe on Windows."""
        mocker.patch(
            "shutil.which",
            return_value="C:\\Program Files\\Microsoft VS Code\\bin\\code.exe",
        )
        result = edit._prepare_editor_command("code.exe")
        assert result == [
            "C:\\Program Files\\Microsoft VS Code\\bin\\code.exe",
            "--wait",
        ]

    def test_vscode_cmd_windows(self, mocker):
        """Should detect code.cmd on Windows."""
        mocker.patch(
            "shutil.which",
            return_value="C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd",
        )
        result = edit._prepare_editor_command("code.cmd")
        assert result == [
            "C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd",
            "--wait",
        ]

    def test_vscode_with_path(self, mocker):
        """Should detect code in full path (absolute paths are used as-is)."""
        # Mock which to handle the path lookup
        mocker.patch("shutil.which", return_value="/usr/local/bin/code")
        # Also mock isabs to treat this as absolute on Windows for testing
        mocker.patch("os.path.isabs", return_value=True)
        result = edit._prepare_editor_command("/usr/local/bin/code")
        assert result == ["/usr/local/bin/code", "--wait"]

    def test_vscode_already_has_wait_flag(self, mocker):
        """Should not add --wait if already present."""
        mocker.patch("shutil.which", return_value="/usr/local/bin/code")
        result = edit._prepare_editor_command("code --wait")
        assert result == ["/usr/local/bin/code", "--wait"]

    def test_vscode_already_has_w_flag(self, mocker):
        """Should not add --wait if -w already present."""
        mocker.patch("shutil.which", return_value="/usr/local/bin/code")
        result = edit._prepare_editor_command("code -w")
        assert result == ["/usr/local/bin/code", "-w"]

    def test_editor_with_code_in_name_but_not_vscode(self, mocker):
        """Should detect 'code' substring in basename."""
        mocker.patch("shutil.which", return_value="/usr/bin/mycode")
        result = edit._prepare_editor_command("mycode")
        assert result == ["/usr/bin/mycode", "--wait"]

    def test_editor_not_found(self, mocker):
        """Should return None if editor is not found in PATH."""
        mocker.patch("shutil.which", return_value=None)
        result = edit._prepare_editor_command("nonexistent")
        assert result is None


class TestEditInTempFile:
    """Tests for edit_in_temp_file function."""

    def test_file_modified(self, mocker, tmp_path):
        """Should return modified content when file is changed."""
        # Create a real temp file to test modification detection
        test_file = tmp_path / "test.md"

        # Mock tempfile to return our test file
        mock_temp = mocker.Mock()
        mock_temp.name = str(test_file)

        # Make write actually write to the file
        def mock_write(content):
            test_file.write_text(content)

        mock_temp.write = mock_write

        mock_temp.__enter__ = mocker.Mock(return_value=mock_temp)
        mock_temp.__exit__ = mocker.Mock()
        mocker.patch("tempfile.NamedTemporaryFile", return_value=mock_temp)

        # Mock os.path.getmtime in the edit module to simulate file modification
        mtime_values = [100.0, 200.0]  # First call returns 100, second returns 200
        mocker.patch("notehub.commands.edit.os.path.getmtime", side_effect=mtime_values)

        # Mock _prepare_editor_command to return a valid command
        mocker.patch("notehub.commands.edit._prepare_editor_command", return_value=["vim"])

        # Mock subprocess.run to modify the file
        def mock_edit(*args, **kwargs):
            # Simulate editor modifying the file
            test_file.write_text("modified content")
            result = mocker.Mock()
            result.returncode = 0
            return result

        mocker.patch("subprocess.run", side_effect=mock_edit)

        result = edit.edit_in_temp_file("original content", "vim")

        assert result == "modified content"

    def test_file_unmodified(self, mocker, tmp_path):
        """Should return None when file is not changed."""
        test_file = tmp_path / "test.md"
        test_file.write_text("original content")

        mock_temp = mocker.Mock()
        mock_temp.name = str(test_file)
        mock_temp.__enter__ = mocker.Mock(return_value=mock_temp)
        mock_temp.__exit__ = mocker.Mock()
        mocker.patch("tempfile.NamedTemporaryFile", return_value=mock_temp)

        # Mock subprocess.run without modifying file
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        result = edit.edit_in_temp_file("original content", "vim")

        assert result is None

    def test_editor_not_found(self, mocker, tmp_path, capsys):
        """Should handle editor not found error."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content")

        mock_temp = mocker.Mock()
        mock_temp.name = str(test_file)
        mock_temp.__enter__ = mocker.Mock(return_value=mock_temp)
        mock_temp.__exit__ = mocker.Mock()
        mocker.patch("tempfile.NamedTemporaryFile", return_value=mock_temp)

        # Mock subprocess to raise FileNotFoundError
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())

        result = edit.edit_in_temp_file("content", "nonexistent")

        assert result is None
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_editor_not_found_windows(self, mocker, tmp_path, capsys):
        """Should show Windows-specific message when editor not found."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content")

        mock_temp = mocker.Mock()
        mock_temp.name = str(test_file)
        mock_temp.__enter__ = mocker.Mock(return_value=mock_temp)
        mock_temp.__exit__ = mocker.Mock()
        mocker.patch("tempfile.NamedTemporaryFile", return_value=mock_temp)

        mocker.patch("subprocess.run", side_effect=FileNotFoundError())
        # Patch sys.platform in the edit module where it's actually used
        mocker.patch("notehub.commands.edit.sys.platform", "win32")
        mocker.patch("shutil.which", return_value="vi.exe")

        result = edit.edit_in_temp_file("content", "vi")

        assert result is None
        captured = capsys.readouterr()
        assert ".exe" in captured.err

    def test_editor_returns_error(self, mocker, tmp_path):
        """Should return None when editor exits with error."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content")

        mock_temp = mocker.Mock()
        mock_temp.name = str(test_file)
        mock_temp.__enter__ = mocker.Mock(return_value=mock_temp)
        mock_temp.__exit__ = mocker.Mock()
        mocker.patch("tempfile.NamedTemporaryFile", return_value=mock_temp)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch("subprocess.run", return_value=mock_result)

        result = edit.edit_in_temp_file("content", "vim")

        assert result is None

    def test_temp_file_cleanup(self, mocker, tmp_path):
        """Should clean up temp file even on error."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content")

        mock_temp = mocker.Mock()
        mock_temp.name = str(test_file)
        mock_temp.__enter__ = mocker.Mock(return_value=mock_temp)
        mock_temp.__exit__ = mocker.Mock()
        mocker.patch("tempfile.NamedTemporaryFile", return_value=mock_temp)

        mocker.patch("subprocess.run", side_effect=FileNotFoundError())
        mock_unlink = mocker.patch("os.unlink")

        edit.edit_in_temp_file("content", "vim")

        mock_unlink.assert_called_once_with(str(test_file))


class TestEditRun:
    """Tests for edit run function."""

    def test_successful_edit(self, mocker, tmp_path):
        """Should launch editor on cached note successfully."""
        # Mock context resolution
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)

        # Mock note ident resolution
        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        # Mock cache operations
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        mocker.patch("notehub.commands.edit.cache.get_cache_path", return_value=cache_path)
        mocker.patch(
            "notehub.commands.edit.cache.get_note_path",
            return_value=cache_path / "note.md",
        )
        mock_ensure = mocker.patch("notehub.commands.edit._ensure_cache_current")

        # Mock editor
        mocker.patch("notehub.commands.edit.get_editor", return_value="vim")
        mocker.patch("notehub.commands.edit._prepare_editor_command", return_value=["vim"])
        mock_launch = mocker.patch("notehub.commands.edit._launch_editor_blocking", return_value=0)

        # Mock auto-sync operations
        mocker.patch("notehub.commands.edit.cache.commit_if_dirty", return_value=False)
        mocker.patch("notehub.commands.edit.cache.get_note_content", return_value="content")
        mocker.patch("notehub.commands.edit.update_issue")
        mocker.patch(
            "notehub.commands.edit.get_issue_metadata",
            return_value={"updated_at": "2025-01-01T00:00:00Z"},
        )
        mock_set_ts = mocker.patch("notehub.commands.edit.cache.set_last_known_updated_at")

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 0
        mock_ensure.assert_called_once()
        mock_launch.assert_called_once()
        mock_set_ts.assert_called_once()

    def test_no_changes_made(self, mocker, tmp_path):
        """Should handle cache creation for new issue."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)

        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        # Mock cache doesn't exist
        cache_path = tmp_path / "cache"
        mocker.patch("notehub.commands.edit.cache.get_cache_path", return_value=cache_path)

        # Mock get_issue for cache init
        mock_issue = {"body": "content", "updated_at": "2025-01-01T00:00:00Z"}
        mocker.patch("notehub.commands.edit.get_issue", return_value=mock_issue)

        mock_init = mocker.patch("notehub.commands.edit.cache.init_cache")
        mocker.patch("notehub.commands.edit.cache.set_last_known_updated_at")
        mocker.patch(
            "notehub.commands.edit.cache.get_note_path",
            return_value=cache_path / "note.md",
        )

        mocker.patch("notehub.commands.edit.get_editor", return_value="vim")
        mocker.patch("notehub.commands.edit._prepare_editor_command", return_value=["vim"])
        mocker.patch("notehub.commands.edit._launch_editor_blocking", return_value=0)

        # Mock auto-sync operations
        mocker.patch("notehub.commands.edit.cache.commit_if_dirty", return_value=False)
        mocker.patch("notehub.commands.edit.cache.get_note_content", return_value="content")
        mocker.patch("notehub.commands.edit.update_issue")
        mocker.patch(
            "notehub.commands.edit.get_issue_metadata",
            return_value={"updated_at": "2025-01-01T00:00:00Z"},
        )
        mock_set_ts2 = mocker.patch("notehub.commands.edit.cache.set_last_known_updated_at")

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 0
        mock_init.assert_called_once()
        # set_last_known_updated_at called twice: once during init, once after sync
        assert mock_set_ts2.call_count == 2

    def test_empty_body_user_confirms(self, mocker, tmp_path):
        """Should handle empty body from GitHub."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)

        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        cache_path = tmp_path / "cache"
        mocker.patch("notehub.commands.edit.cache.get_cache_path", return_value=cache_path)

        # Empty body from GitHub
        mock_issue = {"body": "", "updated_at": "2025-01-01T00:00:00Z"}
        mocker.patch("notehub.commands.edit.get_issue", return_value=mock_issue)

        mock_init = mocker.patch("notehub.commands.edit.cache.init_cache")
        mocker.patch("notehub.commands.edit.cache.set_last_known_updated_at")
        mocker.patch(
            "notehub.commands.edit.cache.get_note_path",
            return_value=cache_path / "note.md",
        )

        mocker.patch("notehub.commands.edit.get_editor", return_value="vim")
        mocker.patch("notehub.commands.edit._prepare_editor_command", return_value=["vim"])
        mocker.patch("notehub.commands.edit._launch_editor_blocking", return_value=0)

        # Mock auto-sync operations
        mocker.patch("notehub.commands.edit.cache.commit_if_dirty", return_value=False)
        mocker.patch("notehub.commands.edit.cache.get_note_content", return_value="")
        mocker.patch("notehub.commands.edit.update_issue")
        mocker.patch(
            "notehub.commands.edit.get_issue_metadata",
            return_value={"updated_at": "2025-01-01T00:00:00Z"},
        )

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 0
        mock_init.assert_called_once_with(cache_path, 42, "")

    def test_empty_body_user_declines(self, mocker, tmp_path):
        """Should handle None body from GitHub."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)

        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        cache_path = tmp_path / "cache"
        mocker.patch("notehub.commands.edit.cache.get_cache_path", return_value=cache_path)

        # None body from GitHub
        mock_issue = {"body": None, "updated_at": "2025-01-01T00:00:00Z"}
        mocker.patch("notehub.commands.edit.get_issue", return_value=mock_issue)

        mock_init = mocker.patch("notehub.commands.edit.cache.init_cache")
        mocker.patch("notehub.commands.edit.cache.set_last_known_updated_at")
        mocker.patch(
            "notehub.commands.edit.cache.get_note_path",
            return_value=cache_path / "note.md",
        )

        mocker.patch("notehub.commands.edit.get_editor", return_value="vim")
        mocker.patch("notehub.commands.edit._prepare_editor_command", return_value=["vim"])
        mocker.patch("notehub.commands.edit._launch_editor_blocking", return_value=0)

        # Mock auto-sync operations
        mocker.patch("notehub.commands.edit.cache.commit_if_dirty", return_value=False)
        mocker.patch("notehub.commands.edit.cache.get_note_content", return_value="")
        mocker.patch("notehub.commands.edit.update_issue")
        mocker.patch(
            "notehub.commands.edit.get_issue_metadata",
            return_value={"updated_at": "2025-01-01T00:00:00Z"},
        )

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 0
        mock_init.assert_called_once_with(cache_path, 42, "")

    def test_keyboard_interrupt_during_confirmation(self, mocker, capsys):
        """Should handle Ctrl+C gracefully."""
        mock_context = mocker.Mock()
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)

        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        # Raise KeyboardInterrupt during cache operations
        mocker.patch(
            "notehub.commands.edit.cache.get_cache_path",
            side_effect=KeyboardInterrupt(),
        )

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Cancelled" in captured.err

    def test_note_ident_resolution_failure(self, mocker, capsys):
        """Should handle note ident resolution error."""
        mock_context = mocker.Mock()
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)

        # Return error from resolve_note_ident
        mocker.patch(
            "notehub.commands.edit.resolve_note_ident",
            return_value=(None, "Note not found"),
        )

        args = Namespace(note_ident="nonexistent")
        result = edit.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Note not found" in captured.err

    def test_gh_error_during_fetch(self, mocker, tmp_path):
        """Should handle GhError during cache initialization."""
        mock_context = mocker.Mock()
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)
        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        cache_path = tmp_path / "cache"
        mocker.patch("notehub.commands.edit.cache.get_cache_path", return_value=cache_path)

        # Mock get_issue to raise GhError
        mocker.patch("notehub.commands.edit.get_issue", side_effect=GhError(1, "API error"))

        # Mock get_issue to raise GhError
        mocker.patch("notehub.commands.edit.get_issue", side_effect=GhError(1, "API error"))

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 1

    def test_gh_error_during_update(self, mocker, tmp_path):
        """Should handle GhError during cache sync."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)

        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        mocker.patch("notehub.commands.edit.cache.get_cache_path", return_value=cache_path)

        # Mock _ensure_cache_current to raise GhError
        mocker.patch(
            "notehub.commands.edit._ensure_cache_current",
            side_effect=GhError(1, "Sync failed"),
        )

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 1

    def test_keyboard_interrupt_during_edit(self, mocker, capsys, tmp_path):
        """Should handle Ctrl+C during editor preparation."""
        mock_context = mocker.Mock()
        mocker.patch("notehub.commands.edit.StoreContext.resolve", return_value=mock_context)
        mocker.patch("notehub.commands.edit.resolve_note_ident", return_value=(42, None))

        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        mocker.patch("notehub.commands.edit.cache.get_cache_path", return_value=cache_path)
        mocker.patch("notehub.commands.edit._ensure_cache_current")

        # Mock get_editor to raise KeyboardInterrupt
        mocker.patch("notehub.commands.edit.get_editor", side_effect=KeyboardInterrupt())

        args = Namespace(note_ident="42")
        result = edit.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Cancelled" in captured.err


class TestAddRun:
    """Tests for add run function."""

    def test_successful_add(self, mocker):
        """Should create issue with notehub label successfully."""
        # Mock context resolution
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.add.StoreContext.resolve", return_value=mock_context)

        # Mock ensure_label_exists to succeed
        mock_ensure = mocker.patch("notehub.commands.add.ensure_label_exists", return_value=True)

        # Mock create_issue to succeed
        mock_create = mocker.patch("notehub.commands.add.create_issue")

        args = Namespace()
        result = add.run(args)

        assert result == 0
        mock_ensure.assert_called_once_with(
            "github.com",
            "testorg",
            "testrepo",
            "notehub",
            "FFC107",
            "Issues created by notehub CLI",
        )
        mock_create.assert_called_once_with("github.com", "testorg", "testrepo", interactive=True, labels=["notehub"])

    def test_label_creation_failure(self, mocker, capsys):
        """Should return error when label creation fails."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.add.StoreContext.resolve", return_value=mock_context)

        # Mock ensure_label_exists to fail
        mocker.patch("notehub.commands.add.ensure_label_exists", return_value=False)

        # Mock create_issue - should not be called
        mock_create = mocker.patch("notehub.commands.add.create_issue")

        args = Namespace()
        result = add.run(args)

        assert result == 1
        mock_create.assert_not_called()
        captured = capsys.readouterr()
        assert "Could not create 'notehub' label" in captured.err

    def test_issue_creation_gh_error(self, mocker):
        """Should handle GhError during issue creation."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch("notehub.commands.add.StoreContext.resolve", return_value=mock_context)

        mocker.patch("notehub.commands.add.ensure_label_exists", return_value=True)

        # Mock create_issue to raise GhError
        mocker.patch("notehub.commands.add.create_issue", side_effect=GhError(1, "API error"))

        args = Namespace()
        result = add.run(args)

        assert result == 1

    def test_context_resolution_integration(self, mocker):
        """Should pass resolved context to gh_wrapper functions."""
        # Test with enterprise host
        mock_context = mocker.Mock()
        mock_context.host = "github.example.com"
        mock_context.org = "mycompany"
        mock_context.repo = "myproject"
        mocker.patch("notehub.commands.add.StoreContext.resolve", return_value=mock_context)

        mock_ensure = mocker.patch("notehub.commands.add.ensure_label_exists", return_value=True)
        mock_create = mocker.patch("notehub.commands.add.create_issue")

        args = Namespace()
        add.run(args)

        # Verify enterprise host was used
        assert mock_ensure.call_args[0][0] == "github.example.com"
        assert mock_create.call_args[0][0] == "github.example.com"


class TestSyncCached:
    """Tests for sync --cached functionality."""

    def test_sync_cached_no_dirty_notes(self, mocker):
        """Should display message when no dirty notes found."""
        from notehub.commands import sync

        mocker.patch("notehub.cache.find_dirty_cached_notes", return_value=[])

        args = Namespace(cached=True, note_ident=None)
        result = sync.run(args)

        assert result == 0

    def test_sync_cached_multiple_notes(self, mocker):
        """Should sync all dirty notes across repos."""
        from pathlib import Path

        from notehub.commands import sync

        # Mock dirty notes from different repos
        dirty_notes = [
            ("github.com", "org1", "repo1", 1, Path("/cache/1")),
            ("github.com", "org1", "repo1", 2, Path("/cache/2")),
            ("github.com", "org2", "repo2", 5, Path("/cache/5")),
        ]
        mocker.patch("notehub.cache.find_dirty_cached_notes", return_value=dirty_notes)
        mocker.patch("notehub.cache.commit_if_dirty", return_value=True)
        mocker.patch("notehub.cache.get_note_content", return_value="test content")
        mock_update = mocker.patch("notehub.commands.sync.update_issue")
        mocker.patch(
            "notehub.commands.sync.get_issue_metadata",
            return_value={"updated_at": "2024-01-01T00:00:00Z"},
        )
        mocker.patch("notehub.cache.set_last_known_updated_at")

        args = Namespace(cached=True, note_ident=None)
        result = sync.run(args)

        assert result == 0
        assert mock_update.call_count == 3

    def test_sync_cached_handles_404(self, mocker, capsys):
        """Should skip deleted issues with warning."""
        from pathlib import Path

        from notehub.commands import sync

        dirty_notes = [
            ("github.com", "org", "repo", 1, Path("/cache/1")),
        ]
        mocker.patch("notehub.cache.find_dirty_cached_notes", return_value=dirty_notes)
        mocker.patch("notehub.cache.commit_if_dirty", return_value=True)
        mocker.patch("notehub.cache.get_note_content", return_value="test content")

        # Mock 404 error
        mocker.patch(
            "notehub.commands.sync.update_issue",
            side_effect=GhError(1, "Not Found: 404"),
        )

        args = Namespace(cached=True, note_ident=None)
        result = sync.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Skipped - issue deleted on GitHub" in captured.out

    def test_sync_cached_handles_other_errors(self, mocker, capsys):
        """Should continue on errors and report failures."""
        from pathlib import Path

        from notehub.commands import sync

        dirty_notes = [
            ("github.com", "org", "repo", 1, Path("/cache/1")),
            ("github.com", "org", "repo", 2, Path("/cache/2")),
        ]
        mocker.patch("notehub.cache.find_dirty_cached_notes", return_value=dirty_notes)
        mocker.patch("notehub.cache.commit_if_dirty", return_value=True)
        mocker.patch("notehub.cache.get_note_content", return_value="test content")

        # First fails, second succeeds
        mock_update = mocker.patch("notehub.commands.sync.update_issue")
        mock_update.side_effect = [
            GhError(1, "Permission denied"),
            None,  # Success
        ]
        mocker.patch(
            "notehub.commands.sync.get_issue_metadata",
            return_value={"updated_at": "2024-01-01T00:00:00Z"},
        )
        mocker.patch("notehub.cache.set_last_known_updated_at")

        args = Namespace(cached=True, note_ident=None)
        result = sync.run(args)

        assert result == 1  # Should return error code
        captured = capsys.readouterr()
        assert "Failed" in captured.err
        assert "Synced 1 note(s)" in captured.out

    def test_sync_cached_mixed_results(self, mocker):
        """Should handle mix of success, 404, and other errors."""
        from pathlib import Path

        from notehub.commands import sync

        dirty_notes = [
            ("github.com", "org", "repo", 1, Path("/cache/1")),  # Success
            ("github.com", "org", "repo", 2, Path("/cache/2")),  # 404
            ("github.com", "org", "repo", 3, Path("/cache/3")),  # Error
        ]
        mocker.patch("notehub.cache.find_dirty_cached_notes", return_value=dirty_notes)
        mocker.patch("notehub.cache.commit_if_dirty", return_value=True)
        mocker.patch("notehub.cache.get_note_content", return_value="test content")

        mock_update = mocker.patch("notehub.commands.sync.update_issue")
        mock_update.side_effect = [
            None,  # Success
            GhError(1, "Not Found: 404"),
            GhError(1, "API rate limit"),
        ]
        mocker.patch(
            "notehub.commands.sync.get_issue_metadata",
            return_value={"updated_at": "2024-01-01T00:00:00Z"},
        )
        mocker.patch("notehub.cache.set_last_known_updated_at")

        args = Namespace(cached=True, note_ident=None)
        result = sync.run(args)

        assert result == 1  # Should fail due to error

    def test_sync_requires_note_ident_without_cached(self, mocker, capsys):
        """Should require note_ident when --cached is not used."""
        from notehub.commands import sync

        args = Namespace(cached=False, note_ident=None)
        result = sync.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "NOTE-IDENT is required" in captured.err

    def test_sync_single_note_still_works(self, mocker):
        """Should still support single-note sync without --cached."""
        from pathlib import Path

        from notehub.commands import sync

        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "org"
        mock_context.repo = "repo"
        mocker.patch("notehub.commands.sync.StoreContext.resolve", return_value=mock_context)
        mocker.patch("notehub.commands.sync.resolve_note_ident", return_value=(1, None))

        cache_path = Path("/cache/1")
        mocker.patch("notehub.cache.get_cache_path", return_value=cache_path)
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("notehub.cache.commit_if_dirty", return_value=False)
        mocker.patch("notehub.cache.get_note_content", return_value="content")
        mock_update = mocker.patch("notehub.commands.sync.update_issue")
        mocker.patch(
            "notehub.commands.sync.get_issue_metadata",
            return_value={"updated_at": "2024-01-01T00:00:00Z"},
        )
        mocker.patch("notehub.cache.set_last_known_updated_at")

        args = Namespace(cached=False, note_ident="1")
        result = sync.run(args)

        assert result == 0
        assert mock_update.call_count == 1

