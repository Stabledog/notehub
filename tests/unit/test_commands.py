"""Unit tests for notehub command modules."""

import json
import os
import pytest
from argparse import Namespace
from notehub.commands import edit, add
from notehub.gh_wrapper import GhError


class TestPrepareEditorCommand:
    """Tests for _prepare_editor_command function."""

    def test_regular_editor(self, mocker):
        """Should return editor as single-item list."""
        mocker.patch('shutil.which', return_value='/usr/bin/vim')
        result = edit._prepare_editor_command('vim')
        assert result == ['/usr/bin/vim']

    def test_vscode_without_flag(self, mocker):
        """Should add --wait flag for VS Code."""
        mocker.patch('shutil.which', return_value='/usr/local/bin/code')
        result = edit._prepare_editor_command('code')
        assert result == ['/usr/local/bin/code', '--wait']

    def test_vscode_exe_windows(self, mocker):
        """Should detect code.exe on Windows."""
        mocker.patch('shutil.which', return_value='C:\\Program Files\\Microsoft VS Code\\bin\\code.exe')
        result = edit._prepare_editor_command('code.exe')
        assert result == ['C:\\Program Files\\Microsoft VS Code\\bin\\code.exe', '--wait']

    def test_vscode_cmd_windows(self, mocker):
        """Should detect code.cmd on Windows."""
        mocker.patch('shutil.which', return_value='C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd')
        result = edit._prepare_editor_command('code.cmd')
        assert result == ['C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd', '--wait']

    def test_vscode_with_path(self, mocker):
        """Should detect code in full path (absolute paths are used as-is)."""
        # Mock which to handle the path lookup
        mocker.patch('shutil.which', return_value='/usr/local/bin/code')
        # Also mock isabs to treat this as absolute on Windows for testing
        mocker.patch('os.path.isabs', return_value=True)
        result = edit._prepare_editor_command('/usr/local/bin/code')
        assert result == ['/usr/local/bin/code', '--wait']

    def test_vscode_already_has_wait_flag(self, mocker):
        """Should not add --wait if already present."""
        mocker.patch('shutil.which', return_value='/usr/local/bin/code')
        result = edit._prepare_editor_command('code --wait')
        assert result == ['/usr/local/bin/code', '--wait']

    def test_vscode_already_has_w_flag(self, mocker):
        """Should not add --wait if -w already present."""
        mocker.patch('shutil.which', return_value='/usr/local/bin/code')
        result = edit._prepare_editor_command('code -w')
        assert result == ['/usr/local/bin/code', '-w']

    def test_editor_with_code_in_name_but_not_vscode(self, mocker):
        """Should detect 'code' substring in basename."""
        mocker.patch('shutil.which', return_value='/usr/bin/mycode')
        result = edit._prepare_editor_command('mycode')
        assert result == ['/usr/bin/mycode', '--wait']

    def test_editor_not_found(self, mocker):
        """Should return None if editor is not found in PATH."""
        mocker.patch('shutil.which', return_value=None)
        result = edit._prepare_editor_command('nonexistent')
        assert result is None


class TestEditInTempFile:
    """Tests for edit_in_temp_file function."""

    def test_file_modified(self, mocker, tmp_path):
        """Should return modified content when file is changed."""
        # Create a real temp file to test modification detection
        test_file = tmp_path / "test.md"
        test_file.write_text("original content")

        # Mock tempfile to return our test file
        mock_temp = mocker.Mock()
        mock_temp.name = str(test_file)
        mock_temp.__enter__ = mocker.Mock(return_value=mock_temp)
        mock_temp.__exit__ = mocker.Mock()
        mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp)

        # Mock subprocess.run to modify the file
        def mock_edit(*args, **kwargs):
            # Simulate editor modifying the file
            test_file.write_text("modified content")
            result = mocker.Mock()
            result.returncode = 0
            return result

        mocker.patch('subprocess.run', side_effect=mock_edit)

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
        mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp)

        # Mock subprocess.run without modifying file
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)

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
        mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp)

        # Mock subprocess to raise FileNotFoundError
        mocker.patch('subprocess.run', side_effect=FileNotFoundError())

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
        mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp)

        mocker.patch('subprocess.run', side_effect=FileNotFoundError())
        mocker.patch('sys.platform', 'win32')

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
        mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch('subprocess.run', return_value=mock_result)

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
        mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp)

        mocker.patch('subprocess.run', side_effect=FileNotFoundError())
        mock_unlink = mocker.patch('os.unlink')

        edit.edit_in_temp_file("content", "vim")

        mock_unlink.assert_called_once_with(str(test_file))


class TestEditRun:
    """Tests for edit run function."""

    def test_successful_edit(self, mocker):
        """Should edit and update issue successfully."""
        # Mock context resolution
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)

        # Mock note ident resolution
        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))

        # Mock get_issue
        mock_issue = {'number': 42, 'body': 'original body'}
        mocker.patch('notehub.commands.edit.get_issue', return_value=mock_issue)

        # Mock get_editor
        mocker.patch('notehub.commands.edit.get_editor', return_value='vim')

        # Mock edit_in_temp_file
        mocker.patch('notehub.commands.edit.edit_in_temp_file', return_value='modified body')

        # Mock update_issue
        mock_update = mocker.patch('notehub.commands.edit.update_issue')

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 0
        mock_update.assert_called_once_with('github.com', 'testorg', 'testrepo', 42, 'modified body')

    def test_no_changes_made(self, mocker):
        """Should handle case when file is not modified."""
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)

        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))
        mocker.patch('notehub.commands.edit.get_issue', return_value={'body': 'content'})
        mocker.patch('notehub.commands.edit.get_editor', return_value='vim')

        # Return None to indicate no changes
        mocker.patch('notehub.commands.edit.edit_in_temp_file', return_value=None)

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 0

    def test_empty_body_user_confirms(self, mocker):
        """Should update when user confirms empty body."""
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)

        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))
        mocker.patch('notehub.commands.edit.get_issue', return_value={'body': 'content'})
        mocker.patch('notehub.commands.edit.get_editor', return_value='vim')
        mocker.patch('notehub.commands.edit.edit_in_temp_file', return_value='   ')  # Empty/whitespace

        # Mock user input to confirm
        mocker.patch('builtins.input', return_value='y')

        mock_update = mocker.patch('notehub.commands.edit.update_issue')

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 0
        mock_update.assert_called_once()

    def test_empty_body_user_declines(self, mocker, capsys):
        """Should not update when user declines empty body."""
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)

        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))
        mocker.patch('notehub.commands.edit.get_issue', return_value={'body': 'content'})
        mocker.patch('notehub.commands.edit.get_editor', return_value='vim')
        mocker.patch('notehub.commands.edit.edit_in_temp_file', return_value='')

        # Mock user input to decline
        mocker.patch('builtins.input', return_value='n')

        mock_update = mocker.patch('notehub.commands.edit.update_issue')

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 0
        mock_update.assert_not_called()
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()

    def test_keyboard_interrupt_during_confirmation(self, mocker, capsys):
        """Should handle Ctrl+C during empty body confirmation."""
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)

        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))
        mocker.patch('notehub.commands.edit.get_issue', return_value={'body': 'content'})
        mocker.patch('notehub.commands.edit.get_editor', return_value='vim')
        mocker.patch('notehub.commands.edit.edit_in_temp_file', return_value='')

        # Mock KeyboardInterrupt during input
        mocker.patch('builtins.input', side_effect=KeyboardInterrupt())

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()

    def test_note_ident_resolution_failure(self, mocker, capsys):
        """Should handle note ident resolution error."""
        mock_context = mocker.Mock()
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)

        # Return error from resolve_note_ident
        mocker.patch('notehub.commands.edit.resolve_note_ident',
                    return_value=(None, 'Note not found'))

        args = Namespace(note_ident='nonexistent')
        result = edit.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert 'Note not found' in captured.err

    def test_gh_error_during_fetch(self, mocker):
        """Should handle GhError during issue fetch."""
        mock_context = mocker.Mock()
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)
        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))

        # Mock get_issue to raise GhError
        mocker.patch('notehub.commands.edit.get_issue', side_effect=GhError(1, 'API error'))

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 1

    def test_gh_error_during_update(self, mocker):
        """Should handle GhError during issue update."""
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)

        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))
        mocker.patch('notehub.commands.edit.get_issue', return_value={'body': 'content'})
        mocker.patch('notehub.commands.edit.get_editor', return_value='vim')
        mocker.patch('notehub.commands.edit.edit_in_temp_file', return_value='modified')

        # Mock update_issue to raise GhError
        mocker.patch('notehub.commands.edit.update_issue', side_effect=GhError(1, 'Update failed'))

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 1

    def test_keyboard_interrupt_during_edit(self, mocker, capsys):
        """Should handle Ctrl+C during edit process."""
        mock_context = mocker.Mock()
        mocker.patch('notehub.commands.edit.StoreContext.resolve', return_value=mock_context)
        mocker.patch('notehub.commands.edit.resolve_note_ident', return_value=(42, None))

        # Mock edit_in_temp_file to raise KeyboardInterrupt
        mocker.patch('notehub.commands.edit.get_issue', return_value={'body': 'content'})
        mocker.patch('notehub.commands.edit.get_editor', return_value='vim')
        mocker.patch('notehub.commands.edit.edit_in_temp_file', side_effect=KeyboardInterrupt())

        args = Namespace(note_ident='42')
        result = edit.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert 'Cancelled' in captured.err


class TestAddRun:
    """Tests for add run function."""

    def test_successful_add(self, mocker):
        """Should create issue with notehub label successfully."""
        # Mock context resolution
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.add.StoreContext.resolve', return_value=mock_context)

        # Mock ensure_label_exists to succeed
        mock_ensure = mocker.patch('notehub.commands.add.ensure_label_exists', return_value=True)

        # Mock create_issue to succeed
        mock_create = mocker.patch('notehub.commands.add.create_issue')

        args = Namespace()
        result = add.run(args)

        assert result == 0
        mock_ensure.assert_called_once_with(
            'github.com', 'testorg', 'testrepo',
            'notehub', 'FFC107', 'Issues created by notehub CLI'
        )
        mock_create.assert_called_once_with(
            'github.com', 'testorg', 'testrepo',
            interactive=True, labels=['notehub']
        )

    def test_label_creation_failure(self, mocker, capsys):
        """Should return error when label creation fails."""
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.add.StoreContext.resolve', return_value=mock_context)

        # Mock ensure_label_exists to fail
        mocker.patch('notehub.commands.add.ensure_label_exists', return_value=False)

        # Mock create_issue - should not be called
        mock_create = mocker.patch('notehub.commands.add.create_issue')

        args = Namespace()
        result = add.run(args)

        assert result == 1
        mock_create.assert_not_called()
        captured = capsys.readouterr()
        assert "Could not create 'notehub' label" in captured.err

    def test_issue_creation_gh_error(self, mocker):
        """Should handle GhError during issue creation."""
        mock_context = mocker.Mock()
        mock_context.host = 'github.com'
        mock_context.org = 'testorg'
        mock_context.repo = 'testrepo'
        mocker.patch('notehub.commands.add.StoreContext.resolve', return_value=mock_context)

        mocker.patch('notehub.commands.add.ensure_label_exists', return_value=True)

        # Mock create_issue to raise GhError
        mocker.patch('notehub.commands.add.create_issue',
                    side_effect=GhError(1, 'API error'))

        args = Namespace()
        result = add.run(args)

        assert result == 1

    def test_context_resolution_integration(self, mocker):
        """Should pass resolved context to gh_wrapper functions."""
        # Test with enterprise host
        mock_context = mocker.Mock()
        mock_context.host = 'github.example.com'
        mock_context.org = 'mycompany'
        mock_context.repo = 'myproject'
        mocker.patch('notehub.commands.add.StoreContext.resolve', return_value=mock_context)

        mock_ensure = mocker.patch('notehub.commands.add.ensure_label_exists', return_value=True)
        mock_create = mocker.patch('notehub.commands.add.create_issue')

        args = Namespace()
        add.run(args)

        # Verify enterprise host was used
        assert mock_ensure.call_args[0][0] == 'github.example.com'
        assert mock_create.call_args[0][0] == 'github.example.com'
