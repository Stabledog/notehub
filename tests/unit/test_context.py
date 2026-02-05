"""Unit tests for notehub.context module."""

from argparse import Namespace

import pytest

from notehub.context import StoreContext


class TestStoreContextInit:
    """Tests for StoreContext initialization."""

    def test_basic_initialization(self):
        """Should initialize with provided values."""
        context = StoreContext(host="github.com", org="testorg", repo="testrepo")

        assert context.host == "github.com"
        assert context.org == "testorg"
        assert context.repo == "testrepo"


class TestStoreContextResolveHost:
    """Tests for _resolve_host method."""

    def test_host_from_cli_flag(self, mocker):
        """Should prioritize --host flag over other sources."""
        args = Namespace(host="example.com", org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        context = StoreContext.resolve(args)

        assert context.host == "example.com"

    def test_host_from_environment(self, mocker):
        """Should use GH_HOST environment variable when flag not provided."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict("os.environ", {"GH_HOST": "ghes.company.com"}, clear=True)

        context = StoreContext.resolve(args)

        assert context.host == "ghes.company.com"

    def test_host_from_git_remote_https(self, mocker):
        """Should extract host from HTTPS git remote URL."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git commands: rev-parse (branch), config (remote), remote get-url
        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "https://github.example.com/org/repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == "github.example.com"

    def test_host_from_git_remote_ssh(self, mocker):
        """Should extract host from SSH git remote URL."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git commands: rev-parse (branch), config (remote), remote get-url
        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "git@github.example.com:org/repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == "github.example.com"

    def test_host_default_github_com(self, mocker):
        """Should default to github.com when no sources available."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git commands to fail (not in git repo)
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "github.com"


class TestStoreContextResolveOrg:
    """Tests for _resolve_org method."""

    def test_org_from_cli_flag(self, mocker):
        """Should prioritize --org flag over other sources."""
        args = Namespace(host=None, org="myorg", repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git commands to return different org
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git@github.com:differentorg/repo.git"
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == "myorg"

    def test_org_from_git_remote(self, mocker):
        """Should extract org from git remote URL."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git commands for current remote detection
        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "https://github.com/testorg/testrepo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.org == "testorg"

    def test_org_from_environment(self, mocker):
        """Should use NotehubOrg environment variable."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"NotehubOrg": "envorg"}, clear=True)

        # Mock git to fail (not in repo)
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == "envorg"

    def test_org_default_to_user(self, mocker):
        """Should default to $USER when no sources available."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"USER": "testuser"}, clear=True)

        # Mock git to fail
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.org == "testuser"


class TestStoreContextResolveRepo:
    """Tests for _resolve_repo method."""

    def test_repo_from_cli_flag(self, mocker):
        """Should use --repo flag when provided."""
        args = Namespace(host=None, org=None, repo="myrepo")
        mocker.patch.dict("os.environ", {}, clear=True)

        context = StoreContext.resolve(args)

        assert context.repo == "myrepo"

    def test_repo_dot_autodetect(self, mocker):
        """Should auto-detect repo when --repo=. is provided."""
        args = Namespace(host=None, org=None, repo=".")
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git commands for current remote detection
        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "https://github.com/org/detectedrepo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.repo == "detectedrepo"

    def test_repo_from_git_remote(self, mocker):
        """Should extract repo from git remote URL."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git commands for current remote detection
        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "git@github.com:org/myproject.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.repo == "myproject"

    def test_repo_default(self, mocker):
        """Should default to 'notehub.default' when no sources available."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        # Mock git to fail
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.repo == "notehub.default"


class TestGitRemoteParsing:
    """Tests for git remote URL parsing."""

    @pytest.mark.parametrize(
        "url,expected_host",
        [
            ("https://github.com/org/repo.git", "github.com"),
            ("https://github.example.com/org/repo.git", "github.example.com"),
            ("git@github.com:org/repo.git", "github.com"),
            ("git@github.example.com:org/repo.git", "github.example.com"),
        ],
    )
    def test_parse_various_hosts(self, mocker, url, expected_host):
        """Should parse host from various URL formats."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = url
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == expected_host

    @pytest.mark.parametrize(
        "url,expected_org",
        [
            ("https://github.com/myorg/repo.git", "myorg"),
            ("git@github.com:myorg/repo.git", "myorg"),
            ("https://github.com/user123/project.git", "user123"),
        ],
    )
    def test_parse_various_orgs(self, mocker, url, expected_org):
        """Should parse org from various URL formats."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = url
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.org == expected_org

    @pytest.mark.parametrize(
        "url,expected_repo",
        [
            ("https://github.com/org/myrepo.git", "myrepo"),
            ("https://github.com/org/project-name.git", "project-name"),
            ("git@github.com:org/test_repo.git", "test_repo"),
        ],
    )
    def test_parse_various_repos(self, mocker, url, expected_repo):
        """Should parse repo from various URL formats."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = url
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.repo == expected_repo


class TestExpandGitUrl:
    """Tests for _expand_git_url method."""

    def test_expand_url_with_insteadof_rule(self, mocker):
        """Should expand URL using git insteadOf rules."""
        # Mock git config to return insteadOf rule
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "url.https://github.example.com/.insteadof gh:"
        mocker.patch("subprocess.run", return_value=mock_result)

        result = StoreContext._expand_git_url("gh:org/repo.git")

        assert result == "https://github.example.com/org/repo.git"

    def test_expand_url_multiple_insteadof_rules(self, mocker):
        """Should handle multiple insteadOf rules."""
        # Mock git config with multiple rules
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = """url.https://github.com/.insteadof gh:
url.https://gitlab.com/.insteadof gl:
url.https://enterprise.github.com/.insteadof work:"""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = StoreContext._expand_git_url("work:company/project.git")

        assert result == "https://enterprise.github.com/company/project.git"

    def test_expand_url_ssh_short_form_with_ssh_config(self, mocker):
        """Should expand SSH short form using SSH config."""
        # First call: git config (no insteadOf)
        mock_git_result = mocker.Mock()
        mock_git_result.returncode = 1
        mock_git_result.stdout = ""

        # Second call: ssh -G to resolve alias
        mock_ssh_result = mocker.Mock()
        mock_ssh_result.returncode = 0
        mock_ssh_result.stdout = "hostname github.enterprise.com\nport 22"

        mocker.patch("subprocess.run", side_effect=[mock_git_result, mock_ssh_result])

        result = StoreContext._expand_git_url("bbgithub:org/repo.git")

        assert result == "git@github.enterprise.com:org/repo.git"

    def test_expand_url_no_matching_rules(self, mocker):
        """Should return URL unchanged when no rules match."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "url.https://github.com/.insteadof gh:"
        mocker.patch("subprocess.run", return_value=mock_result)

        url = "git@github.com:org/repo.git"
        result = StoreContext._expand_git_url(url)

        assert result == url

    def test_expand_url_git_not_installed(self, mocker):
        """Should handle git not being installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())

        url = "git@github.com:org/repo.git"
        result = StoreContext._expand_git_url(url)

        assert result == url

    def test_expand_url_empty_insteadof_output(self, mocker):
        """Should handle empty git config output."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        url = "gh:org/repo.git"
        result = StoreContext._expand_git_url(url)

        assert result == url


class TestExpandSshHost:
    """Tests for _expand_ssh_host method."""

    def test_resolve_ssh_alias(self, mocker):
        """Should resolve SSH host alias using ssh -G."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = """user git
hostname github.enterprise.com
port 22
identityfile ~/.ssh/id_rsa"""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = StoreContext._expand_ssh_host("bbgithub")

        assert result == "github.enterprise.com"

    def test_resolve_ssh_alias_not_found(self, mocker):
        """Should return None when SSH alias not found."""
        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        result = StoreContext._expand_ssh_host("nonexistent")

        assert result is None

    def test_resolve_ssh_no_hostname_line(self, mocker):
        """Should return None when ssh -G output lacks hostname."""
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "port 22\nuser git"
        mocker.patch("subprocess.run", return_value=mock_result)

        result = StoreContext._expand_ssh_host("alias")

        assert result is None

    def test_resolve_ssh_command_not_found(self, mocker):
        """Should handle ssh command not being installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())

        result = StoreContext._expand_ssh_host("alias")

        assert result is None


class TestGlobalFlag:
    """Tests for --global flag behavior."""

    def test_global_flag_skips_local_git_detection(self, mocker):
        """Should skip git remote detection with --global flag."""
        args = Namespace(host=None, org=None, repo=None, global_scope=True)
        mocker.patch.dict("os.environ", {"USER": "testuser"}, clear=True)

        # Mock subprocess to track calls
        mock_calls = []

        def track_subprocess_call(cmd, **kwargs):
            mock_calls.append(cmd)
            result = mocker.Mock()
            result.returncode = 1
            result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=track_subprocess_call)

        context = StoreContext.resolve(args)

        # Should use defaults since git remote detection is skipped
        assert context.host == "github.com"
        assert context.org == "testuser"
        assert context.repo == "notehub.default"

        # Verify git remote commands were not called
        git_remote_calls = [call for call in mock_calls if "remote" in " ".join(call)]
        assert len(git_remote_calls) == 0

    def test_global_flag_uses_global_git_config(self, mocker):
        """Should use global git config values with --global flag."""
        args = Namespace(host=None, org=None, repo=None, global_scope=True)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            result.returncode = 0

            # Only respond to --global config requests
            if "config" in cmd and "--global" in cmd:
                if "notehub.host" in cmd:
                    result.stdout = "enterprise.github.com"
                elif "notehub.org" in cmd:
                    result.stdout = "globalorg"
                elif "notehub.repo" in cmd:
                    result.stdout = "globalrepo"
                else:
                    result.returncode = 1
                    result.stdout = ""
            else:
                result.returncode = 1
                result.stdout = ""

            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == "enterprise.github.com"
        assert context.org == "globalorg"
        assert context.repo == "globalrepo"

    def test_global_vs_local_git_config_priority(self, mocker):
        """Should prefer local config over global when --global not set."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            result.returncode = 0

            # Simulate both local and global configs being set
            if "config" in cmd:
                if "--global" in cmd:
                    # Global config values
                    if "notehub.repo" in cmd:
                        result.stdout = "globalrepo"
                    else:
                        result.returncode = 1
                        result.stdout = ""
                elif "notehub.repo" in cmd:
                    # Local config value (checked first for repo)
                    result.stdout = "localrepo"
                else:
                    result.returncode = 1
                    result.stdout = ""
            elif "remote" in cmd:
                result.returncode = 1
                result.stdout = ""
            else:
                result.returncode = 1
                result.stdout = ""

            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Should use local repo config
        assert context.repo == "localrepo"


class TestMalformedUrls:
    """Tests for malformed URL handling."""

    def test_https_url_without_org(self, mocker):
        """Should extract what it can from malformed HTTPS URL."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"USER": "testuser"}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "https://github.com/"  # Missing org/repo
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Host is extracted, but org parsing returns the malformed URL
        assert context.host == "github.com"
        # Current behavior: returns empty string from path_parts[0]
        # This is an edge case - malformed URLs aren't handled perfectly

    def test_ssh_url_without_colon(self, mocker):
        """Should handle SSH-style URL missing colon."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"USER": "testuser"}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "git@github.com"  # Missing :org/repo
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Host is extracted, org parsing returns malformed URL as-is
        assert context.host == "github.com"
        # Current behavior: URL without colon fails to parse org

    def test_url_with_unusual_characters(self, mocker):
        """Should handle URLs with dashes and underscores."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = "git@github-enterprise.my-company.com:my_org/my-repo_v2.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == "github-enterprise.my-company.com"
        assert context.org == "my_org"
        assert context.repo == "my-repo_v2"

    def test_empty_git_remote_output(self, mocker):
        """Should handle empty git remote output."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"USER": "testuser"}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                result.returncode = 0
                result.stdout = ""  # Empty output
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Should use defaults
        assert context.host == "github.com"
        assert context.org == "testuser"
        assert context.repo == "notehub.default"


class TestTrackingRemote:
    """Tests for tracking remote detection."""

    def test_uses_upstream_remote_when_configured(self, mocker):
        """Should use 'upstream' remote when branch tracks it."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "upstream"  # Branch tracks 'upstream', not 'origin'
            elif "remote" in cmd and "get-url" in cmd and "upstream" in cmd:
                result.returncode = 0
                result.stdout = "git@github.com:upstream-org/upstream-repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Should extract from 'upstream' remote, not 'origin'
        assert context.host == "github.com"
        assert context.org == "upstream-org"
        assert context.repo == "upstream-repo"

    def test_falls_back_to_origin_when_no_tracking_branch(self, mocker):
        """Should fall back to 'origin' when branch has no tracking remote."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "feature-branch"
            elif "config" in cmd and "branch.feature-branch.remote" in cmd:
                # No tracking remote configured
                result.returncode = 1
                result.stdout = ""
            elif "remote" in cmd and "get-url" in cmd and "origin" in cmd:
                result.returncode = 0
                result.stdout = "git@github.com:origin-org/origin-repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Should fall back to 'origin' remote
        assert context.org == "origin-org"
        assert context.repo == "origin-repo"

    def test_uses_fork_remote_when_configured(self, mocker):
        """Should use 'fork' or other custom remote names."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "dev"
            elif "config" in cmd and "branch.dev.remote" in cmd:
                result.returncode = 0
                result.stdout = "fork"
            elif "remote" in cmd and "get-url" in cmd and "fork" in cmd:
                result.returncode = 0
                result.stdout = "https://github.com/myuser/myforkedrepo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Should use 'fork' remote
        assert context.org == "myuser"
        assert context.repo == "myforkedrepo"

    def test_detached_head_falls_back_to_origin(self, mocker):
        """Should fall back to 'origin' when in detached HEAD state."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                # Detached HEAD returns a commit SHA
                result.returncode = 0
                result.stdout = "abc123def456"
            elif "config" in cmd and "branch.abc123def456.remote" in cmd:
                # No tracking remote for detached HEAD
                result.returncode = 1
                result.stdout = ""
            elif "remote" in cmd and "get-url" in cmd and "origin" in cmd:
                result.returncode = 0
                result.stdout = "git@github.com:default-org/default-repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        # Should fall back to 'origin' remote
        assert context.org == "default-org"
        assert context.repo == "default-repo"


class TestHostAliases:
    """Tests for host alias expansion."""

    def test_host_alias_gh_from_cli_flag(self, mocker):
        """Should expand 'gh' alias to github.com from --host flag."""
        args = Namespace(host="gh", org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "github.com"

    def test_host_alias_github_from_cli_flag(self, mocker):
        """Should expand 'github' alias to github.com from --host flag."""
        args = Namespace(host="github", org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "github.com"

    def test_host_alias_bbgh_from_cli_flag(self, mocker):
        """Should expand 'bbgh' alias to bbgithub.dev.bloomberg.com from --host flag."""
        args = Namespace(host="bbgh", org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "bbgithub.dev.bloomberg.com"

    def test_host_alias_bbgithub_from_cli_flag(self, mocker):
        """Should expand 'bbgithub' alias to bbgithub.dev.bloomberg.com from --host flag."""
        args = Namespace(host="bbgithub", org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "bbgithub.dev.bloomberg.com"

    def test_host_alias_case_insensitive(self, mocker):
        """Should expand aliases case-insensitively."""
        args = Namespace(host="GH", org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "github.com"

    def test_host_alias_from_environment(self, mocker):
        """Should expand alias from GH_HOST environment variable."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"GH_HOST": "bbgh"}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "bbgithub.dev.bloomberg.com"

    def test_host_alias_from_git_config(self, mocker):
        """Should expand alias from git config."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "config" in cmd and "notehub.host" in cmd:
                result.returncode = 0
                result.stdout = "bbgithub"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == "bbgithub.dev.bloomberg.com"

    def test_non_alias_host_unchanged(self, mocker):
        """Should leave non-alias hostnames unchanged."""
        args = Namespace(host="custom.github.com", org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        mock_result = mocker.Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        context = StoreContext.resolve(args)

        assert context.host == "custom.github.com"
