import os
import subprocess
import shutil
from typing import Optional
from pathlib import Path
import logging
import git

from app.config import settings

logger = logging.getLogger(__name__)

class GitService:
    """Service for cloning and managing git repositories"""
    
    def __init__(self):
        self.repos_dir = settings.REPOS_DIR
        os.makedirs(self.repos_dir, exist_ok=True)
    
    def clone_repository(self, repo_url: str, project_id: str) -> str:
        """
        Clone a git repository to local storage.
        
        Args:
            repo_url: Git repository URL (HTTPS or SSH)
            project_id: Unique project identifier
            
        Returns:
            Local path to the cloned repository
        """
        local_path = os.path.join(self.repos_dir, project_id)
        
        # Remove existing directory if present
        if os.path.exists(local_path):
            shutil.rmtree(local_path)
        
        try:
            logger.info(f"Cloning repository {repo_url} to {local_path}")
            git.Repo.clone_from(repo_url, local_path)
            logger.info(f"Successfully cloned repository to {local_path}")
            return local_path
        except git.GitCommandError as e:
            logger.error(f"Git clone failed: {e}")
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def pull_latest(self, local_path: str) -> bool:
        """Pull latest changes from remote"""
        try:
            repo = git.Repo(local_path)
            origin = repo.remotes.origin
            origin.pull()
            return True
        except Exception as e:
            logger.error(f"Git pull failed: {e}")
            return False
    
    def get_repo_info(self, local_path: str) -> dict:
        """Get repository information"""
        try:
            repo = git.Repo(local_path)
            return {
                "head_commit": str(repo.head.commit.hexsha),
                "branch": str(repo.active_branch),
                "remote_url": str(repo.remotes.origin.url) if repo.remotes else None,
                "is_dirty": repo.is_dirty(),
            }
        except Exception as e:
            logger.error(f"Failed to get repo info: {e}")
            return {}
    
    def get_file_tree(self, local_path: str, ignore_patterns: list = None) -> list:
        """
        Get file tree of the repository.
        
        Args:
            local_path: Path to the repository
            ignore_patterns: Patterns to ignore (e.g., ['.git', 'node_modules'])
            
        Returns:
            List of file paths
        """
        if ignore_patterns is None:
            ignore_patterns = ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                             '.env', 'dist', 'build', '.next', 'coverage']
        
        files = []
        for root, dirs, filenames in os.walk(local_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_patterns]
            
            for filename in filenames:
                if not filename.startswith('.'):
                    rel_path = os.path.relpath(os.path.join(root, filename), local_path)
                    files.append(rel_path)
        
        return files
    
    def read_file(self, local_path: str, file_path: str) -> Optional[str]:
        """Read a file from the repository"""
        full_path = os.path.join(local_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def delete_repository(self, local_path: str) -> bool:
        """Delete a cloned repository"""
        try:
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete repository: {e}")
            return False

# Singleton
git_service = GitService()
