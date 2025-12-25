"""Unit tests for notehub.gh_wrapper module."""

import json
import pytest
import subprocess
from notehub.gh_wrapper import (
    GhError,
    _prepare_gh_cmd,
    build_repo_arg,
    get_issue,
    list_issues,
    check_gh_auth,
    get_gh_user,
    check_gh_installed,
)


class TestPrepareGhCmd:
    """Tests for _prepare_gh_cmd function."""

    def test_sets_gh_host(self, mocker):
        """Should set GH_HOST to target host."""
        mocker.patch.dict('os.environ', {'GH_TOKEN': 'test-token'}, clear=True)

        cmd, env = _prepare_gh_cmd('github.example.com', ['gh', 'api', 'user'])

        assert env['GH_HOST'] == 'github.example.com'
        assert cmd == ['gh', 'api', 'user']

    def test_token_priority_enterprise_2(self, mocker):
        """Should prioritize GH_ENTERPRISE_TOKEN_2 over others."""
        mocker.patch.dict('os.environ', {
            'GH_TOKEN': 'token1',
            'GH_ENTERPRISE_TOKEN': 'token2',
            'GH_ENTERPRISE_TOKEN_2': 'token3',
        }, clear=True)

        cmd, env = _prepare_gh_cmd('github.com', ['gh', 'api', 'user'])

        assert env['GH_TOKEN'] == 'token3'
        assert env['GH_ENTERPRISE_TOKEN'] == 'token3'

    def test_token_priority_enterprise(self, mocker):
        """Should use GH_ENTERPRISE_TOKEN when TOKEN_2 not available."""
        mocker.patch.dict('os.environ', {
            'GH_TOKEN': 'token1',
            'GH_ENTERPRISE_TOKEN': 'token2',
        }, clear=True)

        cmd, env = _prepare_gh_cmd('github.com', ['gh', 'api', 'user'])

        assert env['GH_TOKEN'] == 'token2'
        assert env['GH_ENTERPRISE_TOKEN'] == 'token2'

    def test_token_priority_gh_token(self, mocker):
        """Should use GH_TOKEN when enterprise tokens not available."""
        mocker.patch.dict('os.environ', {'GH_TOKEN': 'token1'}, clear=True)

        cmd, env = _prepare_gh_cmd('github.com', ['gh', 'api', 'user'])

        assert env['GH_TOKEN'] == 'token1'
        assert env['GH_ENTERPRISE_TOKEN'] == 'token1'

    def test_no_token_available(self, mocker):
        """Should handle case when no token is set."""
        mocker.patch.dict('os.environ', {}, clear=True)

        cmd, env = _prepare_gh_cmd('github.com', ['gh', 'api', 'user'])

        assert 'GH_TOKEN' not in env
        assert env['GH_HOST'] == 'github.com'


class TestBuildRepoArg:
    """Tests for build_repo_arg function."""

    def test_basic_repo_arg(self):
        """Should format org/repo."""
        result = build_repo_arg('github.com', 'testorg', 'testrepo')

        assert result == 'testorg/testrepo'

    def test_enterprise_host(self):
        """Should format org/repo regardless of host."""
        result = build_repo_arg('github.example.com', 'myorg', 'myrepo')

        assert result == 'myorg/myrepo'


class TestGetIssue:
    """Tests for get_issue function."""

    def test_get_issue_success(self, mocker):
        """Should fetch and parse issue JSON."""
        mock_issue = {
            'number': 42,
            'title': 'Test Issue',
            'html_url': 'https://github.com/org/repo/issues/42',
            'body': 'Issue body content'
        }

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(mock_issue)
        mock_result.stderr = ''
        mocker.patch('subprocess.run', return_value=mock_result)

        result = get_issue('github.com', 'testorg', 'testrepo', 42)

        assert result['number'] == 42
        assert result['title'] == 'Test Issue'
        assert 'body' in result

    def test_get_issue_not_found(self, mocker):
        """Should raise GhError when issue not found."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Not found'
        mocker.patch('subprocess.run', return_value=mock_result)

        with pytest.raises(GhError) as exc_info:
            get_issue('github.com', 'testorg', 'testrepo', 999)

        assert exc_info.value.returncode == 1
        assert 'Not found' in exc_info.value.stderr


class TestListIssues:
    """Tests for list_issues function."""

    def test_list_issues_success(self, mocker, sample_gh_issue_list):
        """Should fetch and parse list of issues."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_gh_issue_list)
        mock_result.stderr = ''
        mocker.patch('subprocess.run', return_value=mock_result)

        result = list_issues('github.com', 'testorg', 'testrepo')

        assert len(result) == 2
        assert result[0]['number'] == 42
        assert result[1]['number'] == 43

    def test_list_issues_empty(self, mocker):
        """Should return empty list when no issues found."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = '[]'
        mock_result.stderr = ''
        mocker.patch('subprocess.run', return_value=mock_result)

        result = list_issues('github.com', 'testorg', 'testrepo')

        assert result == []

    def test_list_issues_with_custom_fields(self, mocker):
        """Should use custom fields parameter."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"number": 1, "title": "Test"}]'
        mock_result.stderr = ''
        mock_run = mocker.patch('subprocess.run', return_value=mock_result)

        list_issues('github.com', 'testorg', 'testrepo', fields='number,title')

        # Verify --json argument includes custom fields
        call_args = mock_run.call_args[0][0]
        assert '--json' in call_args
        json_index = call_args.index('--json')
        assert call_args[json_index + 1] == 'number,title'

    def test_list_issues_error(self, mocker):
        """Should raise GhError on failure."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'API error'
        mocker.patch('subprocess.run', return_value=mock_result)

        with pytest.raises(GhError) as exc_info:
            list_issues('github.com', 'testorg', 'testrepo')

        assert exc_info.value.returncode == 1


class TestCheckGhAuth:
    """Tests for check_gh_auth function."""

    def test_auth_success(self, mocker):
        """Should return True when authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = ''
        mocker.patch('subprocess.run', return_value=mock_result)

        result = check_gh_auth('github.com')

        assert result is True

    def test_auth_failure(self, mocker):
        """Should return False when not authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Not authenticated'
        mocker.patch('subprocess.run', return_value=mock_result)

        result = check_gh_auth('github.com')

        assert result is False


class TestGetGhUser:
    """Tests for get_gh_user function."""

    def test_get_user_success(self, mocker):
        """Should return username when authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'testuser\n'
        mock_result.stderr = ''
        mocker.patch('subprocess.run', return_value=mock_result)

        result = get_gh_user('github.com')

        assert result == 'testuser'

    def test_get_user_failure(self, mocker):
        """Should return None when not authenticated."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Not authenticated'
        mocker.patch('subprocess.run', return_value=mock_result)

        result = get_gh_user('github.com')

        assert result is None

    def test_get_user_exception(self, mocker):
        """Should return None on exception."""
        mocker.patch('subprocess.run', side_effect=Exception('Subprocess error'))

        result = get_gh_user('github.com')

        assert result is None


class TestCheckGhInstalled:
    """Tests for check_gh_installed function."""

    def test_gh_installed(self, mocker):
        """Should return True when gh is found."""
        mocker.patch('shutil.which', return_value='/usr/bin/gh')

        result = check_gh_installed()

        assert result is True

    def test_gh_not_installed(self, mocker):
        """Should return False when gh is not found."""
        mocker.patch('shutil.which', return_value=None)

        result = check_gh_installed()

        assert result is False
