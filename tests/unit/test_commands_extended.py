"""Unit tests for additional notehub command modules (show, list, status) and CLI."""

import io
from argparse import Namespace

import pytest

from notehub import cli
from notehub.commands import add, edit, show, status
from notehub.commands import list as list_cmd
from notehub.gh_wrapper import GhError


class TestShowRun:
    """Tests for show run function."""

    def test_show_single_issue_success(self, mocker, capsys):
        """Should display single issue successfully."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"

        mocker.patch(
            "notehub.commands.show.resolve_note_ident", return_value=(42, None)
        )

        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch(
            "notehub.commands.show.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch(
            "notehub.commands.show.resolve_note_ident", return_value=(42, None)
        )

        mock_issue = {
            "number": 42,
            "title": "Test Issue",
            "html_url": "https://github.com/testorg/testrepo/issues/42",
        }
        mocker.patch("notehub.commands.show.get_issue", return_value=mock_issue)
        mocker.patch(
            "notehub.commands.show.format_note_header", return_value="#42: Test Issue"
        )

        args = Namespace(note_idents=["42"])
        result = show.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "#42: Test Issue" in captured.out
        assert "https://github.com/testorg/testrepo/issues/42" in captured.out

    def test_show_multiple_issues(self, mocker, capsys):
        """Should display multiple issues with blank lines between."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch(
            "notehub.commands.show.StoreContext.resolve", return_value=mock_context
        )

        # Mock resolve_note_ident to return different issue numbers
        mocker.patch(
            "notehub.commands.show.resolve_note_ident",
            side_effect=[(42, None), (43, None)],
        )

        mock_issues = [
            {
                "number": 42,
                "title": "First",
                "html_url": "https://github.com/testorg/testrepo/issues/42",
            },
            {
                "number": 43,
                "title": "Second",
                "html_url": "https://github.com/testorg/testrepo/issues/43",
            },
        ]
        mocker.patch("notehub.commands.show.get_issue", side_effect=mock_issues)
        mocker.patch(
            "notehub.commands.show.format_note_header",
            side_effect=["#42: First", "#43: Second"],
        )

        args = Namespace(note_idents=["42", "43"])
        result = show.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "#42: First" in captured.out
        assert "#43: Second" in captured.out

    def test_show_partial_failure(self, mocker, capsys):
        """Should continue processing after error and return error code."""
        mock_context = mocker.Mock()
        mocker.patch(
            "notehub.commands.show.StoreContext.resolve", return_value=mock_context
        )

        # First succeeds, second fails, third succeeds
        mocker.patch(
            "notehub.commands.show.resolve_note_ident",
            side_effect=[(42, None), (None, "Not found"), (44, None)],
        )

        mock_issues = [
            {"number": 42, "title": "First", "html_url": "url1"},
            {"number": 44, "title": "Third", "html_url": "url3"},
        ]
        mocker.patch("notehub.commands.show.get_issue", side_effect=mock_issues)
        mocker.patch(
            "notehub.commands.show.format_note_header",
            side_effect=["#42: First", "#44: Third"],
        )

        args = Namespace(note_idents=["42", "nonexistent", "44"])
        result = show.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Not found" in captured.err

    def test_show_gh_error(self, mocker, capsys):
        """Should handle GhError during issue fetch."""
        mock_context = mocker.Mock()
        mocker.patch(
            "notehub.commands.show.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch(
            "notehub.commands.show.resolve_note_ident", return_value=(42, None)
        )
        mocker.patch(
            "notehub.commands.show.get_issue", side_effect=GhError(1, "API error")
        )

        args = Namespace(note_idents=["42"])
        result = show.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "API error" in captured.err

    def test_show_all_failures(self, mocker, capsys):
        """Should handle all idents failing."""
        mock_context = mocker.Mock()
        mocker.patch(
            "notehub.commands.show.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch(
            "notehub.commands.show.resolve_note_ident",
            side_effect=[(None, "Not found"), (None, "No match")],
        )

        args = Namespace(note_idents=["bad1", "bad2"])
        result = show.run(args)

        assert result == 1


class TestListRun:
    """Tests for list run function."""

    def test_list_success(self, mocker, capsys):
        """Should display all issues."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mocker.patch(
            "notehub.commands.list.StoreContext.resolve", return_value=mock_context
        )

        mock_issues = [
            {"number": 42, "title": "First", "url": "url1"},
            {"number": 43, "title": "Second", "url": "url2"},
        ]
        mocker.patch("notehub.commands.list.list_issues", return_value=mock_issues)
        mocker.patch(
            "notehub.commands.list.format_note_header",
            side_effect=["#42: First", "#43: Second"],
        )

        args = Namespace()
        result = list_cmd.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "#42: First" in captured.out
        assert "url1" in captured.out
        assert "#43: Second" in captured.out
        assert "url2" in captured.out

    def test_list_empty(self, mocker, capsys):
        """Should handle empty issue list."""
        mock_context = mocker.Mock()
        mocker.patch(
            "notehub.commands.list.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch("notehub.commands.list.list_issues", return_value=[])

        args = Namespace()
        result = list_cmd.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_list_gh_error(self, mocker):
        """Should return error code on GhError."""
        mock_context = mocker.Mock()
        mocker.patch(
            "notehub.commands.list.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch(
            "notehub.commands.list.list_issues", side_effect=GhError(1, "API error")
        )

        args = Namespace()
        result = list_cmd.run(args)

        assert result == 1

    def test_list_formatting_consistency(self, mocker, capsys):
        """Should match show command formatting with blank lines."""
        mock_context = mocker.Mock()
        mocker.patch(
            "notehub.commands.list.StoreContext.resolve", return_value=mock_context
        )

        mock_issues = [
            {"number": 1, "title": "A", "url": "u1"},
            {"number": 2, "title": "B", "url": "u2"},
            {"number": 3, "title": "C", "url": "u3"},
        ]
        mocker.patch("notehub.commands.list.list_issues", return_value=mock_issues)
        mocker.patch(
            "notehub.commands.list.format_note_header",
            side_effect=["#1: A", "#2: B", "#3: C"],
        )

        args = Namespace()
        list_cmd.run(args)

        captured = capsys.readouterr()
        lines = captured.out.split("\n")
        # Should have blank line before second and third issues
        assert "#1: A" in lines
        assert "" in lines  # Blank line


class TestStatusRun:
    """Tests for status run function."""

    def test_status_authenticated_with_env(self, mocker, capsys):
        """Should display status when authenticated via appropriate environment token."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mock_context.full_identifier = mocker.Mock(return_value="testorg/testrepo")
        mocker.patch(
            "notehub.commands.status.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch(
            "notehub.commands.status.get_local_repo_path", return_value="/path/to/repo"
        )
        mocker.patch("notehub.commands.status.check_gh_installed", return_value=True)
        # Use GITHUB_TOKEN for github.com (enterprise token would be ignored)
        mocker.patch.dict("os.environ", {"GITHUB_TOKEN": "token"}, clear=True)
        mocker.patch("notehub.commands.status.check_gh_auth", return_value=True)
        mocker.patch("notehub.commands.status.get_gh_user", return_value="testuser")

        args = Namespace()
        result = status.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Store Context:" in captured.out
        assert "github.com" in captured.out
        assert "testorg" in captured.out
        assert "testrepo" in captured.out
        assert "GITHUB_TOKEN" in captured.out
        assert "Authenticated" in captured.out
        assert "testuser" in captured.out

    def test_status_with_enterprise_token_for_github_com(self, mocker, capsys):
        """Should use gh auth when enterprise tokens are set for github.com."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "testorg"
        mock_context.repo = "testrepo"
        mock_context.full_identifier = mocker.Mock(return_value="testorg/testrepo")
        mocker.patch(
            "notehub.commands.status.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch(
            "notehub.commands.status.get_local_repo_path", return_value="/path/to/repo"
        )
        mocker.patch("notehub.commands.status.check_gh_installed", return_value=True)
        # Enterprise token set but should be ignored for github.com
        mocker.patch.dict("os.environ", {"GH_ENTERPRISE_TOKEN_2": "token"}, clear=True)
        mocker.patch("notehub.commands.status.check_gh_auth", return_value=True)
        mocker.patch("notehub.commands.status.get_gh_user", return_value="testuser")

        args = Namespace()
        result = status.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Store Context:" in captured.out
        assert "github.com" in captured.out
        # Should use gh auth, not enterprise token
        assert "gh auth (stored credentials)" in captured.out
        assert "Authenticated" in captured.out
        assert "testuser" in captured.out

    def test_status_not_authenticated(self, mocker, capsys):
        """Should display setup instructions when not authenticated."""
        mock_context = mocker.Mock()
        mock_context.host = "github.example.com"
        mock_context.org = "org"
        mock_context.repo = "repo"
        mock_context.full_identifier = mocker.Mock(
            return_value="github.example.com:org/repo"
        )
        mocker.patch(
            "notehub.commands.status.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch("notehub.commands.status.get_local_repo_path", return_value=None)
        mocker.patch("notehub.commands.status.check_gh_installed", return_value=True)
        mocker.patch.dict("os.environ", {}, clear=True)
        mocker.patch("notehub.commands.status.check_gh_auth", return_value=False)

        args = Namespace()
        result = status.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Not authenticated" in captured.out
        assert "gh auth login --hostname github.example.com" in captured.out
        assert "global context" in captured.out

    def test_status_gh_not_installed(self, mocker, capsys):
        """Should show gh not installed message."""
        mock_context = mocker.Mock()
        mocker.patch(
            "notehub.commands.status.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch("notehub.commands.status.get_local_repo_path", return_value=None)
        mocker.patch("notehub.commands.status.check_gh_installed", return_value=False)

        args = Namespace()
        result = status.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "gh CLI not found" in captured.out
        assert "https://cli.github.com/" in captured.out

    def test_get_env_auth_source_priority(self, mocker):
        """Should return appropriate token env var based on host, or None to use gh auth."""
        # For github.com with GITHUB_TOKEN
        mocker.patch.dict(
            "os.environ",
            {"GITHUB_TOKEN": "token1", "GH_ENTERPRISE_TOKEN_2": "token2"},
            clear=True,
        )
        assert status.get_env_auth_source("github.com") == "GITHUB_TOKEN"

        # For github.com with only GH_TOKEN (no enterprise tokens)
        mocker.patch.dict("os.environ", {"GH_TOKEN": "token"}, clear=True)
        assert status.get_env_auth_source("github.com") == "GH_TOKEN"

        # For github.com with enterprise tokens but no GITHUB_TOKEN - should use gh auth
        mocker.patch.dict(
            "os.environ",
            {"GH_ENTERPRISE_TOKEN_2": "enterprise-token"},
            clear=True,
        )
        assert status.get_env_auth_source("github.com") is None

        # For github.com with GH_TOKEN and enterprise tokens - should use gh auth
        mocker.patch.dict(
            "os.environ",
            {"GH_TOKEN": "token", "GH_ENTERPRISE_TOKEN": "enterprise"},
            clear=True,
        )
        assert status.get_env_auth_source("github.com") is None

        # For enterprise hosts with enterprise tokens
        mocker.patch.dict(
            "os.environ",
            {"GITHUB_TOKEN": "token1", "GH_ENTERPRISE_TOKEN_2": "token2"},
            clear=True,
        )
        assert (
            status.get_env_auth_source("enterprise.github.com")
            == "GH_ENTERPRISE_TOKEN_2"
        )

        mocker.patch.dict("os.environ", {"GH_ENTERPRISE_TOKEN": "token"}, clear=True)
        assert (
            status.get_env_auth_source("enterprise.github.com") == "GH_ENTERPRISE_TOKEN"
        )

        # For enterprise host with only GH_TOKEN (no GITHUB_TOKEN)
        mocker.patch.dict("os.environ", {"GH_TOKEN": "token"}, clear=True)
        assert status.get_env_auth_source("enterprise.github.com") == "GH_TOKEN"

        # For enterprise host with only GITHUB_TOKEN - should use gh auth
        mocker.patch.dict("os.environ", {"GITHUB_TOKEN": "token"}, clear=True)
        assert status.get_env_auth_source("enterprise.github.com") is None

        # No token set
        mocker.patch.dict("os.environ", {}, clear=True)
        assert status.get_env_auth_source() is None

    def test_get_local_repo_path_in_repo(self, mocker):
        """Should return repo path when in git repo."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/home/user/project\n"
        mocker.patch("subprocess.run", return_value=mock_result)

        result = status.get_local_repo_path()

        assert result == "/home/user/project"

    def test_get_local_repo_path_not_in_repo(self, mocker):
        """Should return None when not in git repo."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = status.get_local_repo_path()

        assert result is None

    def test_status_with_local_path(self, mocker, capsys):
        """Should display local repo path when available."""
        mock_context = mocker.Mock()
        mock_context.host = "github.com"
        mock_context.org = "org"
        mock_context.repo = "repo"
        mock_context.full_identifier = mocker.Mock(return_value="org/repo")
        mocker.patch(
            "notehub.commands.status.StoreContext.resolve", return_value=mock_context
        )

        mocker.patch(
            "notehub.commands.status.get_local_repo_path", return_value="/local/path"
        )
        mocker.patch("notehub.commands.status.check_gh_installed", return_value=True)
        mocker.patch.dict("os.environ", {}, clear=True)
        mocker.patch("notehub.commands.status.check_gh_auth", return_value=True)
        mocker.patch("notehub.commands.status.get_gh_user", return_value="user")

        args = Namespace()
        status.run(args)

        captured = capsys.readouterr()
        assert "Path:  /local/path" in captured.out


class TestCLI:
    """Tests for CLI argument parsing and dispatch."""

    def test_create_parser_has_all_commands(self):
        """Should create parser with all subcommands."""
        parser = cli.create_parser()

        # Parse help to check subcommands exist
        import contextlib

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            try:
                parser.parse_args(["--help"])
            except SystemExit:
                pass

        help_text = f.getvalue()
        assert "add" in help_text
        assert "show" in help_text
        assert "list" in help_text
        assert "edit" in help_text
        assert "status" in help_text
        assert "sync" in help_text

    def test_add_command_sets_handler(self):
        """Should set handler for add command."""
        parser = cli.create_parser()
        args = parser.parse_args(["add"])

        assert hasattr(args, "handler")
        assert args.handler == add.run

    def test_show_command_requires_idents(self):
        """Should require at least one note-ident for show."""
        parser = cli.create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["show"])

    def test_show_command_accepts_multiple_idents(self):
        """Should accept multiple note-idents for show."""
        parser = cli.create_parser()
        args = parser.parse_args(["show", "42", "43", "regex"])

        assert args.note_idents == ["42", "43", "regex"]
        assert args.handler == show.run

    def test_edit_command_requires_single_ident(self):
        """Should require exactly one note-ident for edit."""
        parser = cli.create_parser()
        args = parser.parse_args(["edit", "42"])

        assert args.note_ident == "42"
        assert args.handler == edit.run

    def test_common_args_on_all_commands(self):
        """Should accept common store args on all commands."""
        parser = cli.create_parser()

        args = parser.parse_args(
            [
                "add",
                "--host",
                "gh.example.com",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--global",
            ]
        )
        assert args.host == "gh.example.com"
        assert args.org == "myorg"
        assert args.repo == "myrepo"
        assert args.global_scope is True

    def test_global_flag_short_form(self):
        """Should accept -g for --global."""
        parser = cli.create_parser()
        args = parser.parse_args(["status", "-g"])

        assert args.global_scope is True

    def test_main_dispatches_to_handler(self, mocker):
        """Should parse args and call handler."""
        mock_handler = mocker.Mock(return_value=0)
        mocker.patch("notehub.cli.create_parser")

        mock_parser = mocker.Mock()
        mock_parsed = mocker.Mock()
        mock_parsed.handler = mock_handler
        mock_parser.parse_args = mocker.Mock(return_value=mock_parsed)
        cli.create_parser.return_value = mock_parser

        result = cli.main(["add"])

        assert result == 0
        mock_handler.assert_called_once_with(mock_parsed)

    def test_main_returns_handler_exit_code(self, mocker):
        """Should return handler's exit code."""
        mock_handler = mocker.Mock(return_value=1)
        mocker.patch("notehub.cli.create_parser")

        mock_parser = mocker.Mock()
        mock_parsed = mocker.Mock()
        mock_parsed.handler = mock_handler
        mock_parser.parse_args = mocker.Mock(return_value=mock_parsed)
        cli.create_parser.return_value = mock_parser

        result = cli.main(["add"])

        assert result == 1
