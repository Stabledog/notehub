"""Unit tests for notehub.gh_wrapper module."""

import json

import pytest

from notehub.gh_wrapper import (
    GhError,
    _prepare_gh_cmd,
    _run_gh_command,
    build_repo_arg,
    check_gh_auth,
    check_gh_installed,
    get_gh_user,
    get_issue,
    list_issues,
)


class TestPrepareGhCmd:
    """Tests for _prepare_gh_cmd function."""

    def test_sets_gh_host(self, mocker):
        """Should set GH_HOST to target host."""
        mocker.patch.dict("os.environ", {"GH_TOKEN": "test-token"}, clear=True)

        cmd, env = _prepare_gh_cmd("github.example.com", ["gh", "api", "user"])

        assert env["GH_HOST"] == "github.example.com"
        assert cmd == ["gh.sh", "api", "user"]

    def test_converts_gh_to_gh_sh(self, mocker):
        """Should convert 'gh' command to 'gh.sh'."""
        mocker.patch.dict("os.environ", {}, clear=True)

        cmd, env = _prepare_gh_cmd("github.com", ["gh", "issue", "list"])

        assert cmd[0] == "gh.sh"
        assert cmd == ["gh.sh", "issue", "list"]

    def test_preserves_environment(self, mocker):
        """Should preserve existing environment variables."""
        mocker.patch.dict(
            "os.environ",
            {
                "GH_TOKEN": "token1",
                "GH_ENTERPRISE_TOKEN": "token2",
                "GITHUB_TOKEN": "token3",
            },
            clear=True,
        )

        cmd, env = _prepare_gh_cmd("github.com", ["gh", "api", "user"])

        # Env vars should be passed through unchanged - gh.sh handles auth
        assert env["GH_TOKEN"] == "token1"
        assert env["GH_ENTERPRISE_TOKEN"] == "token2"
        assert env["GITHUB_TOKEN"] == "token3"
        assert env["GH_HOST"] == "github.com"

    def test_enterprise_host_sets_gh_host(self, mocker):
        """Should set GH_HOST for enterprise hosts."""
        mocker.patch.dict("os.environ", {}, clear=True)

        cmd, env = _prepare_gh_cmd("github.enterprise.com", ["gh", "api", "user"])

        assert env["GH_HOST"] == "github.enterprise.com"
        assert cmd == ["gh.sh", "api", "user"]


class TestBuildRepoArg:
    """Tests for build_repo_arg function."""

    def test_basic_repo_arg(self):
        """Should format org/repo."""
        result = build_repo_arg("github.com", "testorg", "testrepo")

        assert result == "testorg/testrepo"

    def test_enterprise_host(self):
        """Should format org/repo regardless of host."""
        result = build_repo_arg("github.example.com", "myorg", "myrepo")

        assert result == "myorg/myrepo"


class TestGetIssue:
    """Tests for get_issue function."""

    def test_get_issue_success(self, mocker):
        """Should fetch and parse issue JSON."""
        mock_issue = {
            "number": 42,
            "title": "Test Issue",
            "html_url": "https://github.com/org/repo/issues/42",
            "body": "Issue body content",
        }

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(mock_issue)
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = get_issue("github.com", "testorg", "testrepo", 42)

        assert result["number"] == 42
        assert result["title"] == "Test Issue"
        assert "body" in result

    def test_get_issue_not_found(self, mocker):
        """Should raise GhError when issue not found."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Not found"
        mocker.patch("subprocess.run", return_value=mock_result)

        with pytest.raises(GhError) as exc_info:
            get_issue("github.com", "testorg", "testrepo", 999)

        assert exc_info.value.returncode == 1
        assert "Not found" in exc_info.value.stderr


class TestListIssues:
    """Tests for list_issues function."""

    def test_list_issues_success(self, mocker, sample_gh_issue_list):
        """Should fetch and parse list of issues."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_gh_issue_list)
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = list_issues("github.com", "testorg", "testrepo")

        assert len(result) == 2
        assert result[0]["number"] == 42
        assert result[1]["number"] == 43

    def test_list_issues_empty(self, mocker):
        """Should return empty list when no issues found."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = list_issues("github.com", "testorg", "testrepo")

        assert result == []

    def test_list_issues_with_custom_fields(self, mocker):
        """Should use custom fields parameter."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"number": 1, "title": "Test"}]'
        mock_result.stderr = ""
        mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        list_issues("github.com", "testorg", "testrepo", fields="number,title")

        # Verify --json argument includes custom fields
        call_args = mock_run.call_args[0][0]
        assert "--json" in call_args
        json_index = call_args.index("--json")
        assert call_args[json_index + 1] == "number,title"

    def test_list_issues_error(self, mocker):
        """Should raise GhError on failure."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "API error"
        mocker.patch("subprocess.run", return_value=mock_result)

        with pytest.raises(GhError) as exc_info:
            list_issues("github.com", "testorg", "testrepo")

        assert exc_info.value.returncode == 1


class TestCheckGhAuth:
    """Tests for check_gh_auth function."""

    def test_auth_success(self, mocker):
        """Should return True when authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = check_gh_auth("github.com")

        assert result is True

    def test_auth_failure(self, mocker):
        """Should return False when not authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Not authenticated"
        mocker.patch("subprocess.run", return_value=mock_result)

        result = check_gh_auth("github.com")

        assert result is False


class TestGetGhUser:
    """Tests for get_gh_user function."""

    def test_get_user_success(self, mocker):
        """Should return username when authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "testuser\n"
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = get_gh_user("github.com")

        assert result == "testuser"

    def test_get_user_failure(self, mocker):
        """Should return None when not authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Not authenticated"
        mocker.patch("subprocess.run", return_value=mock_result)

        result = get_gh_user("github.com")

        assert result is None

    def test_get_user_exception(self, mocker):
        """Should return None on exception."""
        mocker.patch("subprocess.run", side_effect=Exception("Subprocess error"))

        result = get_gh_user("github.com")

        assert result is None


class TestCheckGhInstalled:
    """Tests for check_gh_installed function."""

    def test_always_returns_true(self):
        """Should always return True - trusts dotkit setup."""
        result = check_gh_installed()

        assert result is True

    def test_no_validation_performed(self):
        """Should not perform any validation - fail fast approach."""
        # Just verify it returns True without any checks
        result = check_gh_installed()

        assert result is True


class TestCreateIssue:
    """Tests for create_issue function."""

    def test_create_issue_interactive_success(self, mocker):
        """Should invoke gh issue create in interactive mode."""
        from notehub.gh_wrapper import create_issue

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        # Mock stdin/stdout/stderr from sys
        mocker.patch("sys.stdin")
        mocker.patch("sys.stdout")
        mocker.patch("sys.stderr")

        result = create_issue("github.com", "testorg", "testrepo", interactive=True)

        assert result.returncode == 0
        # Verify interactive mode - no capture_output
        call_kwargs = mock_run.call_args[1]
        assert "capture_output" not in call_kwargs
        assert call_kwargs["stdin"] is not None  # sys.stdin
        assert call_kwargs["stdout"] is not None  # sys.stdout
        assert call_kwargs["stderr"] is not None  # sys.stderr

    def test_create_issue_non_interactive(self, mocker):
        """Should capture output in non-interactive mode."""
        from notehub.gh_wrapper import create_issue

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/testorg/testrepo/issues/42"
        mock_result.stderr = ""
        mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        result = create_issue("github.com", "testorg", "testrepo", interactive=False)

        assert result.returncode == 0
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["capture_output"] is True

    def test_create_issue_with_labels(self, mocker):
        """Should include labels in command."""
        from notehub.gh_wrapper import create_issue

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_run = mocker.patch("subprocess.run", return_value=mock_result)
        mocker.patch("sys.stdin")
        mocker.patch("sys.stdout")
        mocker.patch("sys.stderr")

        create_issue("github.com", "testorg", "testrepo", labels=["notehub", "bug"])

        call_args = mock_run.call_args[0][0]
        assert "--label" in call_args
        assert "notehub" in call_args
        assert "bug" in call_args

    def test_create_issue_failure(self, mocker):
        """Should raise GhError on failure."""
        from notehub.gh_wrapper import GhError, create_issue

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch("subprocess.run", return_value=mock_result)
        mocker.patch("sys.stdin")
        mocker.patch("sys.stdout")
        mocker.patch("sys.stderr")

        with pytest.raises(GhError) as exc_info:
            create_issue("github.com", "testorg", "testrepo")

        assert exc_info.value.returncode == 1


class TestEnsureLabelExists:
    """Tests for ensure_label_exists function."""

    def test_label_created_successfully(self, mocker):
        """Should return True when label is created."""
        from notehub.gh_wrapper import ensure_label_exists

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"name": "notehub", "color": "FFC107"}'
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = ensure_label_exists("github.com", "testorg", "testrepo", "notehub", "FFC107", "Notehub label")

        assert result is True

    def test_label_already_exists(self, mocker):
        """Should return True when label already exists."""
        from notehub.gh_wrapper import ensure_label_exists

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = json.dumps(
            {
                "message": "Validation Failed",
                "errors": [{"code": "already_exists", "field": "name"}],
            }
        )
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = ensure_label_exists("github.com", "testorg", "testrepo", "notehub", "FFC107")

        assert result is True

    def test_label_creation_real_error(self, mocker):
        """Should return False on real API error."""
        from notehub.gh_wrapper import ensure_label_exists

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = json.dumps({"message": "API rate limit exceeded"})
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = ensure_label_exists("github.com", "testorg", "testrepo", "notehub", "FFC107")

        assert result is False

    def test_label_creation_invalid_json(self, mocker):
        """Should return False when stdout is not valid JSON."""
        from notehub.gh_wrapper import ensure_label_exists

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = "Invalid JSON response"
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = ensure_label_exists("github.com", "testorg", "testrepo", "notehub", "FFC107")

        assert result is False


class TestUpdateIssue:
    """Tests for update_issue function."""

    def test_update_issue_success(self, mocker):
        """Should update issue body and return result."""
        from notehub.gh_wrapper import update_issue

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Issue updated"
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = update_issue("github.com", "testorg", "testrepo", 42, "New body content")

        assert result.returncode == 0
        assert result.stdout == "Issue updated"

    def test_update_issue_command_format(self, mocker):
        """Should format gh.sh issue edit command correctly."""
        from notehub.gh_wrapper import update_issue

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        update_issue("github.com", "testorg", "testrepo", 123, "Updated body")

        call_args = mock_run.call_args[0][0]
        assert "gh.sh" in call_args
        assert "issue" in call_args
        assert "edit" in call_args
        assert "123" in call_args
        assert "--body" in call_args
        assert "Updated body" in call_args

    def test_update_issue_failure(self, mocker):
        """Should raise GhError on failure."""
        from notehub.gh_wrapper import GhError, update_issue

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Issue not found"
        mocker.patch("subprocess.run", return_value=mock_result)

        with pytest.raises(GhError) as exc_info:
            update_issue("github.com", "testorg", "testrepo", 999, "Body")

        assert exc_info.value.returncode == 1
        assert "Issue not found" in exc_info.value.stderr


# TestHandleGhError removed - _handle_gh_error function no longer exists
# Error handling is now delegated to gh.sh which provides its own error messages


class TestRunGhCommand:
    """Tests for _run_gh_command wrapper function."""

    def test_successful_command(self, mocker):
        """Should execute command successfully with capture_output."""
        mock_run = mocker.patch("notehub.gh_wrapper.subprocess.run")
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"key": "value"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = _run_gh_command(["gh", "api", "user"], {}, "github.com")

        assert result.returncode == 0
        assert result.stdout == '{"key": "value"}'
        mock_run.assert_called_once()
        # Check that errors='replace' is passed
        assert mock_run.call_args[1]["errors"] == "replace"

    # Error handling tests removed - we now fail fast and don't catch errors
    # gh.sh provides its own error messages

    def test_passthrough_mode(self, mocker):
        """Should handle passthrough mode without capture_output."""
        mock_run = mocker.patch("notehub.gh_wrapper.subprocess.run")
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _run_gh_command(
            ["gh", "issue", "create"],
            {},
            "github.com",
            capture_output=False,
            stdin=None,
            stdout=None,
            stderr=None,
        )

        assert result.returncode == 0
        # Should not pass errors='replace' in passthrough mode
        assert "errors" not in mock_run.call_args[1]


class TestListIssuesErrorHandling:
    """Tests for list_issues error handling."""

    def test_handles_empty_response(self, mocker, capsys):
        """Should handle None/empty stdout from gh command."""
        mock_run = mocker.patch("notehub.gh_wrapper.subprocess.run")
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = None
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with pytest.raises(GhError):
            list_issues("github.com", "test-org", "test-repo")

        captured = capsys.readouterr()
        assert "No response from GitHub server" in captured.err
        assert "github.com" in captured.err

    def test_handles_invalid_json(self, mocker, capsys):
        """Should handle invalid JSON response."""
        mock_run = mocker.patch("notehub.gh_wrapper.subprocess.run")
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "not valid json"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with pytest.raises(GhError):
            list_issues("github.com", "test-org", "test-repo")

        captured = capsys.readouterr()
        assert "Invalid response from GitHub server" in captured.err
        assert "github.com" in captured.err
