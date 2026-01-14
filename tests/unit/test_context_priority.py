"""Unit tests for new context resolution priority order."""

from argparse import Namespace

import pytest

from notehub.context import StoreContext


class TestHostResolutionPriority:
    """Tests for new host resolution priority order."""

    def test_host_local_git_config_beats_auto_detect(self, mocker):
        """Should prefer local git config over auto-detect from remote."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "config" in cmd and "notehub.host" in cmd and "--global" not in cmd:
                # Local git config returns custom host
                result.returncode = 0
                result.stdout = "local.github.com"
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote would give different host
                result.returncode = 0
                result.stdout = "https://remote.github.com/org/repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == "local.github.com"

    def test_host_auto_detect_beats_global_git_config(self, mocker):
        """Should prefer auto-detect from remote over global git config."""
        args = Namespace(org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "config" in cmd and "notehub.host" in cmd:
                if "--global" in cmd:
                    # Global git config returns fallback host
                    result.returncode = 0
                    result.stdout = "global.github.com"
                else:
                    # Local git config not set
                    result.returncode = 1
                    result.stdout = ""
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote gives auto-detected host
                result.returncode = 0
                result.stdout = "https://autodetect.github.com/org/repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.host == "autodetect.github.com"


class TestOrgResolutionPriority:
    """Tests for new org resolution priority order."""

    def test_org_local_git_config_beats_auto_detect(self, mocker):
        """Should prefer local git config over auto-detect from remote."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "config" in cmd and "notehub.org" in cmd and "--global" not in cmd:
                # Local git config returns custom org
                result.returncode = 0
                result.stdout = "localorg"
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote would give different org
                result.returncode = 0
                result.stdout = "https://github.com/remoteorg/repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.org == "localorg"

    def test_org_env_var_beats_auto_detect(self, mocker):
        """Should prefer environment variable over auto-detect from remote."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"NotehubOrg": "envorg"}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote would give different org
                result.returncode = 0
                result.stdout = "https://github.com/autodetectorg/repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.org == "envorg"

    def test_org_auto_detect_beats_global_git_config(self, mocker):
        """Should prefer auto-detect from remote over global git config."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "config" in cmd and "notehub.org" in cmd:
                if "--global" in cmd:
                    # Global git config returns fallback org
                    result.returncode = 0
                    result.stdout = "globalorg"
                else:
                    # Local git config not set
                    result.returncode = 1
                    result.stdout = ""
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote gives auto-detected org
                result.returncode = 0
                result.stdout = "https://github.com/autodetectorg/repo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.org == "autodetectorg"


class TestRepoResolutionPriority:
    """Tests for new repo resolution priority order."""

    def test_repo_local_git_config_beats_auto_detect(self, mocker):
        """Should prefer local git config over auto-detect from remote."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "config" in cmd and "notehub.repo" in cmd and "--global" not in cmd:
                # Local git config returns custom repo
                result.returncode = 0
                result.stdout = "localrepo"
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote would give different repo
                result.returncode = 0
                result.stdout = "https://github.com/org/remoterepo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.repo == "localrepo"

    def test_repo_env_var_beats_auto_detect(self, mocker):
        """Should prefer environment variable over auto-detect from remote."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {"NotehubRepo": "envrepo"}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote would give different repo
                result.returncode = 0
                result.stdout = "https://github.com/org/autodetectrepo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.repo == "envrepo"

    def test_repo_auto_detect_beats_global_git_config(self, mocker):
        """Should prefer auto-detect from remote over global git config."""
        args = Namespace(host=None, org=None, repo=None)
        mocker.patch.dict("os.environ", {}, clear=True)

        def mock_git_call(cmd, **kwargs):
            result = mocker.Mock()
            if "config" in cmd and "notehub.repo" in cmd:
                if "--global" in cmd:
                    # Global git config returns fallback repo
                    result.returncode = 0
                    result.stdout = "globalrepo"
                else:
                    # Local git config not set
                    result.returncode = 1
                    result.stdout = ""
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.returncode = 0
                result.stdout = "main"
            elif "config" in cmd and "branch.main.remote" in cmd:
                result.returncode = 0
                result.stdout = "origin"
            elif "remote" in cmd and "get-url" in cmd:
                # Remote gives auto-detected repo
                result.returncode = 0
                result.stdout = "https://github.com/org/autodetectrepo.git"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        mocker.patch("subprocess.run", side_effect=mock_git_call)

        context = StoreContext.resolve(args)

        assert context.repo == "autodetectrepo"
