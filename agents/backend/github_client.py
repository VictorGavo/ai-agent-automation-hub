# agents/backend/github_client.py
"""GitHub integration for branch management and PR creation"""

import asyncio
import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone

from github import Github, GithubException
from github.Repository import Repository
from github.GitRef import GitRef
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest

logger = logging.getLogger(__name__)

class GitHubClient:
    """
    Handles all GitHub operations for the Backend Agent:
    - Branch creation and management
    - File modifications and commits
    - Pull request creation
    - Repository status checks
    """
    
    def __init__(self):
        """Initialize with GitHub token from environment and set repository details from config"""
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO", "VictorGavo/ai-agent-automation-hub")
        self.github_client: Optional[Github] = None
        self.repo: Optional[Repository] = None
        self.default_branch = "main"
        
        # GitHub operation statistics
        self.stats = {
            "branches_created": 0,
            "commits_made": 0,
            "prs_created": 0,
            "files_modified": 0,
            "operations_failed": 0
        }
        
        logger.info(f"GitHub client initialized for repository: {self.github_repo}")
    
    async def initialize(self) -> bool:
        """Initialize GitHub client connection"""
        try:
            if not self.github_token:
                logger.warning("GitHub token not found - GitHub integration disabled")
                return False
            
            # Initialize GitHub client
            self.github_client = Github(self.github_token)
            
            # Get repository
            self.repo = self.github_client.get_repo(self.github_repo)
            
            # Get default branch
            self.default_branch = self.repo.default_branch
            
            # Test connection
            repo_info = {
                "name": self.repo.name,
                "full_name": self.repo.full_name,
                "default_branch": self.default_branch,
                "private": self.repo.private
            }
            
            logger.info(f"GitHub client connected successfully: {repo_info}")
            return True
            
        except GithubException as e:
            logger.error(f"GitHub API error during initialization: {e}")
            self.stats["operations_failed"] += 1
            return False
        except Exception as e:
            logger.error(f"GitHub client initialization failed: {e}")
            self.stats["operations_failed"] += 1
            return False
    
    async def create_branch(self, branch_name: str, base_branch: str = None) -> Optional[str]:
        """
        Create new branch from base branch
        
        Args:
            branch_name: Name of the new branch to create
            base_branch: Base branch to create from (defaults to repository default)
            
        Returns:
            Branch name if successful, None if failed
        """
        if not self.repo:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            # Use default branch if base_branch not specified
            if base_branch is None:
                base_branch = self.default_branch
            
            # Get base branch reference
            base_ref = self.repo.get_branch(base_branch)
            base_sha = base_ref.commit.sha
            
            # Create new branch
            new_ref = self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_sha
            )
            
            self.stats["branches_created"] += 1
            logger.info(f"Created branch '{branch_name}' from '{base_branch}' (SHA: {base_sha[:8]})")
            return branch_name
            
        except GithubException as e:
            if e.status == 422:  # Branch already exists
                logger.info(f"Branch '{branch_name}' already exists")
                return branch_name
            else:
                logger.error(f"GitHub API error creating branch '{branch_name}': {e}")
                self.stats["operations_failed"] += 1
                return None
        except Exception as e:
            logger.error(f"Failed to create branch '{branch_name}': {e}")
            self.stats["operations_failed"] += 1
            return None
    
    async def commit_changes(self, branch_name: str, files: Dict[str, str], commit_message: str) -> bool:
        """
        Commit multiple file changes to branch
        
        Args:
            branch_name: Target branch for the commit
            files: Dictionary of file_path -> file_content
            commit_message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            logger.error("GitHub client not initialized")
            return False
        
        if not files:
            logger.warning("No files provided for commit")
            return False
        
        try:
            # Get branch reference
            branch_ref = self.repo.get_git_ref(f"heads/{branch_name}")
            
            # Get the latest commit on the branch
            latest_commit = self.repo.get_git_commit(branch_ref.object.sha)
            
            # Create blobs for all files
            blobs = []
            for file_path, content in files.items():
                blob = self.repo.create_git_blob(content, "utf-8")
                blobs.append({
                    "path": file_path,
                    "mode": "100644",  # Regular file mode
                    "type": "blob",
                    "sha": blob.sha
                })
            
            # Create tree with all files
            tree = self.repo.create_git_tree(blobs, latest_commit.tree)
            
            # Create commit
            commit = self.repo.create_git_commit(
                message=commit_message,
                tree=tree,
                parents=[latest_commit]
            )
            
            # Update branch reference
            branch_ref.edit(commit.sha)
            
            self.stats["commits_made"] += 1
            self.stats["files_modified"] += len(files)
            
            logger.info(f"Committed {len(files)} files to branch '{branch_name}': {commit_message}")
            logger.debug(f"Files committed: {list(files.keys())}")
            
            return True
            
        except GithubException as e:
            logger.error(f"GitHub API error committing to branch '{branch_name}': {e}")
            self.stats["operations_failed"] += 1
            return False
        except Exception as e:
            logger.error(f"Failed to commit changes to branch '{branch_name}': {e}")
            self.stats["operations_failed"] += 1
            return False
    
    async def create_pull_request(self, branch_name: str, title: str, description: str, 
                                base_branch: str = None) -> Optional[str]:
        """
        Create PR from feature branch to base branch
        
        Args:
            branch_name: Source branch for the PR
            title: PR title
            description: PR description with task details and success criteria
            base_branch: Target branch (defaults to repository default)
            
        Returns:
            PR URL if successful, None if failed
        """
        if not self.repo:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            # Use default branch if base_branch not specified
            if base_branch is None:
                base_branch = self.default_branch
            
            # Create pull request
            pr = self.repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=base_branch
            )
            
            self.stats["prs_created"] += 1
            
            logger.info(f"Created pull request #{pr.number}: {title}")
            logger.info(f"PR URL: {pr.html_url}")
            
            return pr.html_url
            
        except GithubException as e:
            logger.error(f"GitHub API error creating pull request: {e}")
            self.stats["operations_failed"] += 1
            return None
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            self.stats["operations_failed"] += 1
            return None
    
    async def get_file_content(self, file_path: str, branch: str = None) -> Optional[str]:
        """
        Get current file content for modification
        
        Args:
            file_path: Path to the file in the repository
            branch: Branch to get file from (defaults to repository default)
            
        Returns:
            File content as string if found, None if not found or error
        """
        if not self.repo:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            # Use default branch if branch not specified
            if branch is None:
                branch = self.default_branch
            
            # Get file content
            file_content = self.repo.get_contents(file_path, ref=branch)
            
            # Handle if it's a file (not directory)
            if isinstance(file_content, ContentFile):
                content = file_content.decoded_content.decode('utf-8')
                logger.debug(f"Retrieved file content: {file_path} from branch '{branch}'")
                return content
            else:
                logger.warning(f"Path '{file_path}' is a directory, not a file")
                return None
                
        except GithubException as e:
            if e.status == 404:
                logger.info(f"File '{file_path}' not found in branch '{branch}'")
                return None
            else:
                logger.error(f"GitHub API error getting file '{file_path}': {e}")
                self.stats["operations_failed"] += 1
                return None
        except Exception as e:
            logger.error(f"Failed to get file content '{file_path}': {e}")
            self.stats["operations_failed"] += 1
            return None
    
    async def update_file(self, file_path: str, content: str, commit_message: str, 
                         branch_name: str) -> bool:
        """
        Update a single file in the repository
        
        Args:
            file_path: Path to the file to update
            content: New file content
            commit_message: Commit message for the update
            branch_name: Branch to update the file in
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            logger.error("GitHub client not initialized")
            return False
        
        try:
            # Try to get existing file
            try:
                existing_file = self.repo.get_contents(file_path, ref=branch_name)
                # Update existing file
                self.repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=branch_name
                )
                logger.info(f"Updated existing file: {file_path} in branch '{branch_name}'")
            except GithubException as e:
                if e.status == 404:
                    # Create new file
                    self.repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        branch=branch_name
                    )
                    logger.info(f"Created new file: {file_path} in branch '{branch_name}'")
                else:
                    raise
            
            self.stats["files_modified"] += 1
            return True
            
        except GithubException as e:
            logger.error(f"GitHub API error updating file '{file_path}': {e}")
            self.stats["operations_failed"] += 1
            return False
        except Exception as e:
            logger.error(f"Failed to update file '{file_path}': {e}")
            self.stats["operations_failed"] += 1
            return False
    
    async def branch_exists(self, branch_name: str) -> bool:
        """
        Check if a branch exists in the repository
        
        Args:
            branch_name: Name of the branch to check
            
        Returns:
            True if branch exists, False otherwise
        """
        if not self.repo:
            logger.error("GitHub client not initialized")
            return False
        
        try:
            self.repo.get_branch(branch_name)
            return True
        except GithubException as e:
            if e.status == 404:
                return False
            else:
                logger.error(f"Error checking if branch '{branch_name}' exists: {e}")
                return False
        except Exception as e:
            logger.error(f"Failed to check if branch '{branch_name}' exists: {e}")
            return False
    
    async def delete_branch(self, branch_name: str) -> bool:
        """
        Delete a branch from the repository
        
        Args:
            branch_name: Name of the branch to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.repo:
            logger.error("GitHub client not initialized")
            return False
        
        try:
            # Don't allow deletion of default branch
            if branch_name == self.default_branch:
                logger.error(f"Cannot delete default branch '{branch_name}'")
                return False
            
            # Delete branch reference
            branch_ref = self.repo.get_git_ref(f"heads/{branch_name}")
            branch_ref.delete()
            
            logger.info(f"Deleted branch '{branch_name}'")
            return True
            
        except GithubException as e:
            if e.status == 404:
                logger.info(f"Branch '{branch_name}' does not exist")
                return True  # Consider this success since the goal is achieved
            else:
                logger.error(f"GitHub API error deleting branch '{branch_name}': {e}")
                self.stats["operations_failed"] += 1
                return False
        except Exception as e:
            logger.error(f"Failed to delete branch '{branch_name}': {e}")
            self.stats["operations_failed"] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get GitHub client operation statistics
        
        Returns:
            Dictionary with operation statistics
        """
        return {
            "client_initialized": self.github_client is not None,
            "repository": self.github_repo,
            "default_branch": self.default_branch,
            "operations": self.stats.copy(),
            "success_rate": self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of GitHub operations"""
        total_operations = sum(self.stats.values())
        if total_operations == 0:
            return 100.0
        
        successful_operations = total_operations - self.stats["operations_failed"]
        return (successful_operations / total_operations) * 100.0
    
    async def close(self):
        """Clean up GitHub client resources"""
        if self.github_client:
            # PyGithub doesn't require explicit cleanup, but we can log closure
            logger.info("GitHub client session closed")
            self.github_client = None
            self.repo = None

# Utility functions for common GitHub operations

def sanitize_branch_name(name: str) -> str:
    """
    Sanitize a string to be used as a GitHub branch name
    
    Args:
        name: Original string
        
    Returns:
        Sanitized branch name
    """
    import re
    
    # Replace invalid characters with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9\-_./]', '-', name)
    
    # Remove consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "feature"
    
    # Limit length to reasonable size
    if len(sanitized) > 50:
        sanitized = sanitized[:50].rstrip('-')
    
    return sanitized

def generate_pr_description(task_title: str, task_description: str, 
                          success_criteria: List[str], agent_name: str,
                          execution_time: float = None) -> str:
    """
    Generate a comprehensive PR description
    
    Args:
        task_title: Title of the task
        task_description: Description of the task
        success_criteria: List of success criteria
        agent_name: Name of the agent that created the PR
        execution_time: Time taken to complete the task (in hours)
        
    Returns:
        Formatted PR description
    """
    description = f"""
## 🤖 Automated Backend Implementation

**Task:** {task_title}

### Description
{task_description}

### Changes Made
- ✅ Implemented backend functionality as requested
- ✅ Added comprehensive error handling
- ✅ Created corresponding unit tests
- ✅ Followed project coding standards

### Success Criteria
"""
    
    for i, criteria in enumerate(success_criteria, 1):
        description += f"{i}. [ ] {criteria}\n"
    
    if not success_criteria:
        description += "- [ ] Implementation meets task requirements\n"
        description += "- [ ] Code follows project conventions\n"
        description += "- [ ] Tests provide adequate coverage\n"
    
    description += f"""

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass  
- [ ] Manual testing completed

### Review Checklist
- [ ] Code follows project conventions
- [ ] Error handling is comprehensive
- [ ] Documentation is updated
- [ ] Security considerations addressed

### Automation Details
- **Created by:** {agent_name}
- **Generated on:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    if execution_time is not None:
        description += f"- **Execution time:** {execution_time:.2f} hours\n"
    
    description += "\n---\n*This PR was automatically created by the AI Agent Automation Hub*"
    
    return description