"""Store context resolution - determine host/org/repo from flags, config, and environment."""

from argparse import Namespace
from typing import Optional
import os
import subprocess


class StoreContext:
    """Resolved store context (host/org/repo)."""
    
    def __init__(self, host: str, org: str, repo: str):
        """
        Initialize store context.
        
        Args:
            host: GitHub host (e.g., 'github.com' or GHES hostname)
            org: Organization/owner name
            repo: Repository name
        """
        self.host = host
        self.org = org
        self.repo = repo
    
    @classmethod
    def resolve(cls, args: Namespace) -> 'StoreContext':
        """
        Resolve context from args, config, env, defaults.
        
        Resolution order per spec:
        - Repo: --repo > git config notehub.repo (local unless --global) > 
                env NotehubRepo > git config --global notehub.repo > 
                'notehub.default'
        - Org: --org > auto-detect from git remote (unless --global) > 
               env NotehubOrg > git config --global notehub.org > 
               $USER
        - Host: --host > auto-detect from git remote (unless --global) > 
                git config --global notehub.host > 'github.com'
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            StoreContext: Resolved context
        """
        global_only = getattr(args, 'global_scope', False)
        
        # Resolve host
        host = cls._resolve_host(args, global_only)
        
        # Resolve org
        org = cls._resolve_org(args, global_only)
        
        # Resolve repo
        repo = cls._resolve_repo(args, global_only)
        
        return cls(host, org, repo)
    
    @classmethod
    def _resolve_host(cls, args: Namespace, global_only: bool) -> str:
        """Resolve host from args, git remote, config, or default."""
        # 1. --host flag
        if hasattr(args, 'host') and args.host:
            return args.host
        
        # 2. Auto-detect from git remote (unless --global)
        if not global_only:
            remote_host = cls._get_git_remote_host()
            if remote_host:
                return remote_host
        
        # 3. git config --global notehub.host
        git_host = cls._get_git_config('notehub.host', global_only=True)
        if git_host:
            return git_host
        
        # 4. Default to github.com
        return 'github.com'
    
    @classmethod
    def _resolve_org(cls, args: Namespace, global_only: bool) -> str:
        """Resolve org from args, git remote, env, config, or $USER."""
        # 1. --org flag
        if hasattr(args, 'org') and args.org:
            return args.org
        
        # 2. Auto-detect from git remote (unless --global)
        if not global_only:
            remote_org = cls._get_git_remote_org()
            if remote_org:
                return remote_org
        
        # 3. Environment variable NotehubOrg
        env_org = os.environ.get('NotehubOrg')
        if env_org:
            return env_org
        
        # 4. git config --global notehub.org
        git_org = cls._get_git_config('notehub.org', global_only=True)
        if git_org:
            return git_org
        
        # 5. Default to $USER
        return os.environ.get('USER', 'unknown-user')
    
    @classmethod
    def _resolve_repo(cls, args: Namespace, global_only: bool) -> str:
        """Resolve repo from args, config, env, or default."""
        # 1. --repo flag
        if hasattr(args, 'repo') and args.repo:
            return args.repo
        
        # 2. git config notehub.repo (local unless --global)
        if not global_only:
            local_repo = cls._get_git_config('notehub.repo', global_only=False)
            if local_repo:
                return local_repo
        
        # 3. Environment variable NotehubRepo
        env_repo = os.environ.get('NotehubRepo')
        if env_repo:
            return env_repo
        
        # 4. git config --global notehub.repo
        global_repo = cls._get_git_config('notehub.repo', global_only=True)
        if global_repo:
            return global_repo
        
        # 5. Default to 'notehub.default'
        return 'notehub.default'
    
    @staticmethod
    def _get_git_config(key: str, global_only: bool = False) -> Optional[str]:
        """
        Get git config value.
        
        Args:
            key: Config key (e.g., 'notehub.host')
            global_only: If True, only check global config
            
        Returns:
            Config value or None if not set
        """
        cmd = ['git', 'config']
        if global_only:
            cmd.append('--global')
        cmd.append(key)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            # git not installed
            pass
        
        return None
    
    @staticmethod
    def _get_git_remote_host() -> Optional[str]:
        """
        Extract host from git remote origin URL.
        
        Returns:
            Host (e.g., 'github.com') or None if not detectable
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse URL - handle both HTTPS and SSH formats
                # HTTPS: https://github.com/org/repo.git
                # SSH: git@github.com:org/repo.git
                if url.startswith('https://'):
                    # Extract host from https://host/...
                    parts = url.split('//')
                    if len(parts) > 1:
                        host_part = parts[1].split('/')[0]
                        return host_part
                elif '@' in url:
                    # Extract host from git@host:...
                    host_part = url.split('@')[1].split(':')[0]
                    return host_part
        except FileNotFoundError:
            pass
        
        return None
    
    @staticmethod
    def _get_git_remote_org() -> Optional[str]:
        """
        Extract org from git remote origin URL.
        
        Returns:
            Organization name or None if not detectable
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse URL
                # HTTPS: https://github.com/org/repo.git -> org
                # SSH: git@github.com:org/repo.git -> org
                if url.startswith('https://'):
                    parts = url.split('//')
                    if len(parts) > 1:
                        path_parts = parts[1].split('/')[1:]  # Skip host
                        if path_parts:
                            return path_parts[0]
                elif ':' in url and '@' in url:
                    # SSH format
                    path = url.split(':')[1]
                    org = path.split('/')[0]
                    return org
        except FileNotFoundError:
            pass
        
        return None
    
    def repo_identifier(self) -> str:
        """
        Return 'org/repo' string.
        
        Returns:
            str: Organization and repository name
        """
        return f"{self.org}/{self.repo}"
    
    def full_identifier(self) -> str:
        """
        Return 'host:org/repo' string (or just 'org/repo' for github.com).
        
        Returns:
            str: Full identifier with host
        """
        if self.host == "github.com":
            return self.repo_identifier()
        return f"{self.host}:{self.repo_identifier()}"
    
    def build_issue_url(self, issue_number: int) -> str:
        """
        Build full GitHub issue URL.
        
        Args:
            issue_number: Issue number
            
        Returns:
            str: Full URL like https://github.com/org/repo/issues/123
        """
        return f"https://{self.host}/{self.org}/{self.repo}/issues/{issue_number}"

