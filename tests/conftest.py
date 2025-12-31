"""Shared pytest fixtures for notehub tests."""

import json
from typing import Dict

import pytest


@pytest.fixture
def mock_env(mocker):
    """
    Fixture to mock os.environ with clean state.

    Usage:
        def test_something(mock_env):
            mock_env({'GH_TOKEN': 'test-token', 'EDITOR': 'vim'})
    """

    def _mock_env(env_dict: Dict[str, str] = None):
        if env_dict is None:
            env_dict = {}
        # Start with empty environment
        mocker.patch.dict("os.environ", env_dict, clear=True)
        return env_dict

    return _mock_env


@pytest.fixture
def mock_subprocess(mocker):
    """
    Fixture to mock subprocess.run calls.

    Usage:
        def test_something(mock_subprocess):
            mock_subprocess(returncode=0, stdout='output')
    """

    def _mock_subprocess(returncode=0, stdout="", stderr="", side_effect=None):
        mock_result = mocker.Mock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr

        if side_effect:
            mock_run = mocker.patch("subprocess.run", side_effect=side_effect)
        else:
            mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        return mock_run

    return _mock_subprocess


@pytest.fixture
def sample_gh_issue():
    """Sample GitHub issue JSON response."""
    return {
        "number": 42,
        "title": "Test Issue",
        "body": "This is a test issue body",
        "state": "open",
        "html_url": "https://github.com/testorg/testrepo/issues/42",
        "labels": [{"name": "notehub"}],
        "user": {"login": "testuser"},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_gh_issue_list(sample_gh_issue):
    """Sample list of GitHub issues."""
    issue1 = sample_gh_issue.copy()
    issue2 = sample_gh_issue.copy()
    issue2["number"] = 43
    issue2["title"] = "Another Test Issue"
    return [issue1, issue2]


@pytest.fixture
def git_remote_urls():
    """Common git remote URL patterns for testing."""
    return {
        "https": "https://github.com/testorg/testrepo.git",
        "https_no_git": "https://github.com/testorg/testrepo",
        "ssh": "git@github.com:testorg/testrepo.git",
        "ssh_no_git": "git@github.com:testorg/testrepo",
        "scp_style": "github.com:testorg/testrepo.git",
        "ghes_https": "https://github.example.com/testorg/testrepo.git",
        "ghes_ssh": "git@github.example.com:testorg/testrepo.git",
    }


@pytest.fixture
def mock_git_commands(mocker):
    """
    Fixture to mock git commands with common responses.

    Usage:
        def test_something(mock_git_commands):
            mock_git_commands(remote='origin', url='https://github.com/org/repo.git')
    """

    def _mock_git(
        remote="origin",
        url="https://github.com/testorg/testrepo.git",
        in_git_repo=True,
        git_config=None,
        current_branch="main",
    ):
        def git_run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])

            # Mock git rev-parse --abbrev-ref HEAD (get current branch)
            if "rev-parse" in cmd and "--abbrev-ref" in cmd and "HEAD" in cmd:
                result = mocker.Mock()
                result.returncode = 0 if in_git_repo else 128
                result.stdout = current_branch if in_git_repo else ""
                result.stderr = "" if in_git_repo else "Not a git repository"
                return result

            # Mock git config branch.<branch>.remote (get tracking remote)
            if "config" in cmd and "branch." in cmd[-1] and ".remote" in cmd[-1]:
                result = mocker.Mock()
                result.returncode = 0 if in_git_repo else 1
                result.stdout = remote if in_git_repo else ""
                result.stderr = ""
                return result

            # Mock git remote get-url <remote>
            if "remote" in cmd and "get-url" in cmd:
                result = mocker.Mock()
                result.returncode = 0 if in_git_repo else 1
                result.stdout = url if in_git_repo else ""
                result.stderr = "" if in_git_repo else "Not a git repository"
                return result

            # Mock git rev-parse --show-toplevel
            if "rev-parse" in cmd and "--show-toplevel" in cmd:
                result = mocker.Mock()
                result.returncode = 0 if in_git_repo else 128
                result.stdout = "/path/to/repo" if in_git_repo else ""
                result.stderr = "" if in_git_repo else "Not a git repository"
                return result

            # Mock git config
            if "config" in cmd and "--get" in cmd:
                result = mocker.Mock()
                key = cmd[-1]
                if git_config and key in git_config:
                    result.returncode = 0
                    result.stdout = git_config[key]
                    result.stderr = ""
                else:
                    result.returncode = 1
                    result.stdout = ""
                    result.stderr = ""
                return result

            # Default: command not found
            result = mocker.Mock()
            result.returncode = 1
            result.stdout = ""
            result.stderr = "Command not mocked"
            return result

        return mocker.patch("subprocess.run", side_effect=git_run_side_effect)

    return _mock_git


@pytest.fixture
def mock_gh_cli(mocker):
    """
    Fixture to mock gh CLI commands with common responses.

    Usage:
        def test_something(mock_gh_cli, sample_gh_issue):
            mock_gh_cli(issue=sample_gh_issue)
    """

    def _mock_gh(
        issue=None, issue_list=None, auth_status="Logged in", username="testuser"
    ):
        def gh_run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args", [])

            # Mock gh issue view
            if "issue" in cmd and "view" in cmd:
                result = mocker.Mock()
                if issue:
                    result.returncode = 0
                    result.stdout = json.dumps(issue)
                    result.stderr = ""
                else:
                    result.returncode = 1
                    result.stdout = ""
                    result.stderr = "Issue not found"
                return result

            # Mock gh issue list
            if "issue" in cmd and "list" in cmd:
                result = mocker.Mock()
                result.returncode = 0
                result.stdout = json.dumps(issue_list or [])
                result.stderr = ""
                return result

            # Mock gh auth status
            if "auth" in cmd and "status" in cmd:
                result = mocker.Mock()
                result.returncode = 0
                result.stdout = auth_status
                result.stderr = ""
                return result

            # Mock gh api user
            if "api" in cmd and "user" in cmd:
                result = mocker.Mock()
                result.returncode = 0
                result.stdout = json.dumps({"login": username})
                result.stderr = ""
                return result

            # Default: success
            result = mocker.Mock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        return mocker.patch("subprocess.run", side_effect=gh_run_side_effect)

    return _mock_gh
