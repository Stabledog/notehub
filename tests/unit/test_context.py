"""Unit tests for notehub.context module."""

import pytest
from argparse import Namespace
from notehub.context import StoreContext


class TestStoreContextInit:
    """Tests for StoreContext initialization."""

    def test_basic_initialization(self):
        """Should initialize with provided values."""
        context = StoreContext(host='github.com', org='testorg', repo='testrepo')

        assert context.host == 'github.com'
        assert context.org == 'testorg'
        assert context.repo == 'testrepo'


class TestStoreContextResolveHost:
    """Tests for _resolve_host method."""

    def test_host_from_cli_flag(self, mocker):
        """Should prioritize --host flag over other sources."""
        args = Namespace(host='example.com', org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        context = StoreContext.resolve(args)

        assert context.host == 'example.com'

    def test_host_from_environment(self, mocker):
        """Should use GH_HOST environment variable when flag not provided."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict('os.environ', {'GH_HOST': 'ghes.company.com'}, clear=True)

        context = StoreContext.resolve(args)

        assert context.host == 'ghes.company.com'

    def test_host_from_git_remote_https(self, mocker):
        """Should extract host from HTTPS git remote URL."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git remote get-url to return HTTPS URL
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'https://github.example.com/org/repo.git'
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == 'github.example.com'

    def test_host_from_git_remote_ssh(self, mocker):
        """Should extract host from SSH git remote URL."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git remote get-url to return SSH URL
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'git@github.example.com:org/repo.git'
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == 'github.example.com'

    def test_host_default_github_com(self, mocker):
        """Should default to github.com when no sources available."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git commands to fail (not in git repo)
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == 'github.com'


class TestStoreContextResolveOrg:
    """Tests for _resolve_org method."""

    def test_org_from_cli_flag(self, mocker):
        """Should prioritize --org flag over other sources."""
        args = Namespace(host=None, org='myorg', repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git commands to return different org
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'git@github.com:differentorg/repo.git'
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == 'myorg'

    def test_org_from_git_remote(self, mocker):
        """Should extract org from git remote URL."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git remote get-url
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'https://github.com/testorg/testrepo.git'
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == 'testorg'

    def test_org_from_environment(self, mocker):
        """Should use NotehubOrg environment variable."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {'NotehubOrg': 'envorg'}, clear=True)

        # Mock git to fail (not in repo)
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == 'envorg'

    def test_org_default_to_user(self, mocker):
        """Should default to $USER when no sources available."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {'USER': 'testuser'}, clear=True)

        # Mock git to fail
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == 'testuser'


class TestStoreContextResolveRepo:
    """Tests for _resolve_repo method."""

    def test_repo_from_cli_flag(self, mocker):
        """Should use --repo flag when provided."""
        args = Namespace(host=None, org=None, repo='myrepo')
        mocker.patch.dict('os.environ', {}, clear=True)

        context = StoreContext.resolve(args)

        assert context.repo == 'myrepo'

    def test_repo_dot_autodetect(self, mocker):
        """Should auto-detect repo when --repo=. is provided."""
        args = Namespace(host=None, org=None, repo='.')
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git remote get-url
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'https://github.com/org/detectedrepo.git'
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.repo == 'detectedrepo'

    def test_repo_from_git_remote(self, mocker):
        """Should extract repo from git remote URL."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git remote get-url
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'git@github.com:org/myproject.git'
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.repo == 'myproject'

    def test_repo_default(self, mocker):
        """Should default to 'notehub.default' when no sources available."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        # Mock git to fail
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.repo == 'notehub.default'


class TestGitRemoteParsing:
    """Tests for git remote URL parsing."""

    @pytest.mark.parametrize('url,expected_host', [
        ('https://github.com/org/repo.git', 'github.com'),
        ('https://github.example.com/org/repo.git', 'github.example.com'),
        ('git@github.com:org/repo.git', 'github.com'),
        ('git@github.example.com:org/repo.git', 'github.example.com'),
    ])
    def test_parse_various_hosts(self, mocker, url, expected_host):
        """Should parse host from various URL formats."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = url
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == expected_host

    @pytest.mark.parametrize('url,expected_org', [
        ('https://github.com/myorg/repo.git', 'myorg'),
        ('git@github.com:myorg/repo.git', 'myorg'),
        ('https://github.com/user123/project.git', 'user123'),
    ])
    def test_parse_various_orgs(self, mocker, url, expected_org):
        """Should parse org from various URL formats."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = url
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == expected_org

    @pytest.mark.parametrize('url,expected_repo', [
        ('https://github.com/org/myrepo.git', 'myrepo'),
        ('https://github.com/org/project-name.git', 'project-name'),
        ('git@github.com:org/test_repo.git', 'test_repo'),
    ])
    def test_parse_various_repos(self, mocker, url, expected_repo):
        """Should parse repo from various URL formats."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict('os.environ', {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = url
        mocker.patch('subprocess.run', return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.repo == expected_repo
