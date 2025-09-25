"""
Safe Git Operations

Provides safe git operations for AI agents with backup branches, 
atomic operations, and rollback capabilities.
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import json
import re
import tempfile
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitOperationType(Enum):
    """Types of git operations."""
    CREATE_BRANCH = "create_branch"
    COMMIT = "commit"
    MERGE = "merge"
    REVERT = "revert"
    ROLLBACK = "rollback"


class GitOperationStatus(Enum):
    """Status of git operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class GitOperation:
    """Represents a git operation with rollback capability."""
    operation_id: str
    operation_type: GitOperationType
    timestamp: datetime
    agent_name: str
    description: str
    status: GitOperationStatus
    branch_name: str
    backup_branch: Optional[str] = None
    original_commit: Optional[str] = None
    files_modified: List[str] = None
    rollback_commands: List[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type.value,
            'timestamp': self.timestamp.isoformat(),
            'agent_name': self.agent_name,
            'description': self.description,
            'status': self.status.value,
            'branch_name': self.branch_name,
            'backup_branch': self.backup_branch,
            'original_commit': self.original_commit,
            'files_modified': self.files_modified or [],
            'rollback_commands': self.rollback_commands or [],
            'error_message': self.error_message
        }


class SafeGitOperations:
    """
    Manages safe git operations for AI agents.
    
    Features:
    - Creates backup branches before modifications
    - Atomic operations (all-or-nothing)
    - Git hooks to prevent direct main branch modifications
    - One-command rollback to last working state
    - Operation logging and audit trail
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize safe git operations.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = os.path.abspath(repo_path)
        self.operations_log_file = os.path.join(self.repo_path, ".git", "operations.json")
        
        # Verify we're in a git repository
        if not self._is_git_repo():
            raise ValueError(f"Not a git repository: {repo_path}")
        
        # Initialize operations log
        self._init_operations_log()
        
        # Install git hooks
        self._install_git_hooks()
        
        logger.info(f"SafeGitOperations initialized for: {self.repo_path}")
    
    def _is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            result = self._run_git_command(['rev-parse', '--git-dir'])
            return result.returncode == 0
        except Exception:
            return False
    
    def _run_git_command(self, args: List[str], check: bool = False) -> subprocess.CompletedProcess:
        """
        Run git command in repository.
        
        Args:
            args: Git command arguments
            check: Whether to raise exception on failure
            
        Returns:
            CompletedProcess result
        """
        cmd = ['git'] + args
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        
        return result
    
    def _init_operations_log(self) -> None:
        """Initialize operations log file."""
        if not os.path.exists(self.operations_log_file):
            os.makedirs(os.path.dirname(self.operations_log_file), exist_ok=True)
            with open(self.operations_log_file, 'w') as f:
                json.dump([], f)
    
    def _log_operation(self, operation: GitOperation) -> None:
        """Log git operation."""
        try:
            # Read existing operations
            operations = []
            if os.path.exists(self.operations_log_file):
                with open(self.operations_log_file, 'r') as f:
                    operations = json.load(f)
            
            # Add new operation
            operations.append(operation.to_dict())
            
            # Keep only last 100 operations
            operations = operations[-100:]
            
            # Write back
            with open(self.operations_log_file, 'w') as f:
                json.dump(operations, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to log operation: {e}")
    
    def _install_git_hooks(self) -> None:
        """Install git hooks to prevent unsafe operations."""
        hooks_dir = os.path.join(self.repo_path, '.git', 'hooks')
        os.makedirs(hooks_dir, exist_ok=True)
        
        # Pre-commit hook to prevent direct main branch commits
        pre_commit_hook = os.path.join(hooks_dir, 'pre-commit')
        hook_content = '''#!/bin/bash
# AI Agent Automation Hub - Safe Git Operations Hook

# Get current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Prevent direct commits to main/master
if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
    echo "❌ Direct commits to $current_branch branch are not allowed!"
    echo "   Please create a feature branch first:"
    echo "   git checkout -b agent-work-$(date +%Y%m%d-%H%M%S)"
    echo "   Then commit your changes and create a PR."
    exit 1
fi

# Check if this is an agent operation
if [[ "$current_branch" =~ ^agent-.* ]] || [[ "$current_branch" =~ ^backup-.* ]]; then
    echo "✅ Agent operation on branch: $current_branch"
fi

exit 0
'''
        
        try:
            with open(pre_commit_hook, 'w') as f:
                f.write(hook_content)
            
            # Make executable
            os.chmod(pre_commit_hook, 0o755)
            
            logger.info("Installed git pre-commit hook")
        
        except Exception as e:
            logger.warning(f"Failed to install git hook: {e}")
    
    def get_current_branch(self) -> str:
        """Get current git branch."""
        result = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    
    def get_current_commit(self) -> str:
        """Get current commit hash."""
        result = self._run_git_command(['rev-parse', 'HEAD'])
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    
    def get_modified_files(self) -> List[str]:
        """Get list of modified files."""
        result = self._run_git_command(['diff', '--name-only', 'HEAD'])
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        return []
    
    def create_backup_branch(self, agent_name: str, description: str = "") -> str:
        """
        Create backup branch before agent operations.
        
        Args:
            agent_name: Name of the agent
            description: Operation description
            
        Returns:
            Backup branch name
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_branch = f"backup-{agent_name}-{timestamp}"
        
        try:
            # Create backup branch from current HEAD
            self._run_git_command(['checkout', '-b', backup_branch], check=True)
            
            # Switch back to original branch
            original_branch = self.get_current_branch()
            if original_branch != backup_branch:
                self._run_git_command(['checkout', '-'], check=True)
            
            logger.info(f"Created backup branch: {backup_branch}")
            return backup_branch
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create backup branch: {e}")
            raise
    
    def create_agent_branch(self, agent_name: str, task_description: str) -> Tuple[str, str]:
        """
        Create safe working branch for agent.
        
        Args:
            agent_name: Name of the agent
            task_description: Description of the task
            
        Returns:
            Tuple of (agent_branch, backup_branch)
        """
        # Create backup first
        backup_branch = self.create_backup_branch(agent_name, "Pre-work backup")
        
        # Create agent working branch
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        agent_branch = f"agent-{agent_name}-{timestamp}"
        
        try:
            # Ensure we're on main/master
            main_branches = ['main', 'master']
            current_branch = self.get_current_branch()
            
            if current_branch not in main_branches:
                # Try to switch to main
                for branch in main_branches:
                    result = self._run_git_command(['checkout', branch])
                    if result.returncode == 0:
                        break
            
            # Create and switch to agent branch
            self._run_git_command(['checkout', '-b', agent_branch], check=True)
            
            # Log operation
            operation = GitOperation(
                operation_id=f"create-{agent_branch}",
                operation_type=GitOperationType.CREATE_BRANCH,
                timestamp=datetime.now(timezone.utc),
                agent_name=agent_name,
                description=f"Created agent branch for: {task_description}",
                status=GitOperationStatus.COMPLETED,
                branch_name=agent_branch,
                backup_branch=backup_branch,
                original_commit=self.get_current_commit()
            )
            self._log_operation(operation)
            
            logger.info(f"Created agent branch: {agent_branch} (backup: {backup_branch})")
            return agent_branch, backup_branch
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create agent branch: {e}")
            raise
    
    def atomic_commit(
        self,
        agent_name: str,
        message: str,
        files: Optional[List[str]] = None,
        allow_empty: bool = False
    ) -> GitOperation:
        """
        Perform atomic commit with rollback capability.
        
        Args:
            agent_name: Name of the agent
            message: Commit message
            files: Specific files to commit (None for all)
            allow_empty: Allow empty commits
            
        Returns:
            GitOperation record
        """
        operation_id = f"commit-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        current_branch = self.get_current_branch()
        original_commit = self.get_current_commit()
        
        operation = GitOperation(
            operation_id=operation_id,
            operation_type=GitOperationType.COMMIT,
            timestamp=datetime.now(timezone.utc),
            agent_name=agent_name,
            description=message,
            status=GitOperationStatus.PENDING,
            branch_name=current_branch,
            original_commit=original_commit,
            files_modified=files or self.get_modified_files()
        )
        
        try:
            operation.status = GitOperationStatus.IN_PROGRESS
            
            # Stage files
            if files:
                for file in files:
                    self._run_git_command(['add', file], check=True)
            else:
                self._run_git_command(['add', '.'], check=True)
            
            # Create commit
            commit_args = ['commit', '-m', f"[{agent_name}] {message}"]
            if allow_empty:
                commit_args.append('--allow-empty')
            
            result = self._run_git_command(commit_args)
            
            if result.returncode == 0:
                new_commit = self.get_current_commit()
                operation.status = GitOperationStatus.COMPLETED
                operation.rollback_commands = [f"git reset --hard {original_commit}"]
                
                logger.info(f"Atomic commit successful: {new_commit}")
            else:
                operation.status = GitOperationStatus.FAILED
                operation.error_message = result.stderr
                logger.error(f"Commit failed: {result.stderr}")
        
        except Exception as e:
            operation.status = GitOperationStatus.FAILED
            operation.error_message = str(e)
            logger.error(f"Atomic commit error: {e}")
        
        finally:
            self._log_operation(operation)
        
        return operation
    
    def rollback_to_commit(self, commit_hash: str, agent_name: str) -> GitOperation:
        """
        Rollback to specific commit.
        
        Args:
            commit_hash: Target commit hash
            agent_name: Name of the agent performing rollback
            
        Returns:
            GitOperation record
        """
        operation_id = f"rollback-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        current_commit = self.get_current_commit()
        
        operation = GitOperation(
            operation_id=operation_id,
            operation_type=GitOperationType.ROLLBACK,
            timestamp=datetime.now(timezone.utc),
            agent_name=agent_name,
            description=f"Rollback to commit {commit_hash[:8]}",
            status=GitOperationStatus.PENDING,
            branch_name=self.get_current_branch(),
            original_commit=current_commit
        )
        
        try:
            operation.status = GitOperationStatus.IN_PROGRESS
            
            # Verify target commit exists
            result = self._run_git_command(['rev-parse', '--verify', commit_hash])
            if result.returncode != 0:
                raise ValueError(f"Invalid commit hash: {commit_hash}")
            
            # Perform rollback
            self._run_git_command(['reset', '--hard', commit_hash], check=True)
            
            operation.status = GitOperationStatus.COMPLETED
            operation.rollback_commands = [f"git reset --hard {current_commit}"]
            
            logger.info(f"Rollback successful to: {commit_hash}")
        
        except Exception as e:
            operation.status = GitOperationStatus.FAILED
            operation.error_message = str(e)
            logger.error(f"Rollback error: {e}")
        
        finally:
            self._log_operation(operation)
        
        return operation
    
    def rollback_to_backup(self, backup_branch: str, agent_name: str) -> GitOperation:
        """
        Rollback to backup branch.
        
        Args:
            backup_branch: Backup branch name
            agent_name: Name of the agent
            
        Returns:
            GitOperation record
        """
        operation_id = f"rollback-backup-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        operation = GitOperation(
            operation_id=operation_id,
            operation_type=GitOperationType.ROLLBACK,
            timestamp=datetime.now(timezone.utc),
            agent_name=agent_name,
            description=f"Rollback to backup branch {backup_branch}",
            status=GitOperationStatus.PENDING,
            branch_name=self.get_current_branch(),
            backup_branch=backup_branch,
            original_commit=self.get_current_commit()
        )
        
        try:
            operation.status = GitOperationStatus.IN_PROGRESS
            
            # Verify backup branch exists
            result = self._run_git_command(['rev-parse', '--verify', f'refs/heads/{backup_branch}'])
            if result.returncode != 0:
                raise ValueError(f"Backup branch not found: {backup_branch}")
            
            # Switch to backup branch
            self._run_git_command(['checkout', backup_branch], check=True)
            
            operation.status = GitOperationStatus.COMPLETED
            logger.info(f"Rollback to backup branch successful: {backup_branch}")
        
        except Exception as e:
            operation.status = GitOperationStatus.FAILED
            operation.error_message = str(e)
            logger.error(f"Rollback to backup error: {e}")
        
        finally:
            self._log_operation(operation)
        
        return operation
    
    def get_rollback_options(self) -> Dict[str, Any]:
        """
        Get available rollback options.
        
        Returns:
            Dictionary with rollback options
        """
        options = {
            'current_branch': self.get_current_branch(),
            'current_commit': self.get_current_commit(),
            'backup_branches': [],
            'recent_commits': [],
            'operations_history': []
        }
        
        try:
            # Get backup branches
            result = self._run_git_command(['branch', '--list', 'backup-*'])
            if result.returncode == 0:
                branches = [b.strip().replace('* ', '') for b in result.stdout.split('\n') if b.strip()]
                options['backup_branches'] = branches
            
            # Get recent commits
            result = self._run_git_command(['log', '--oneline', '-10'])
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1] if len(parts) > 1 else ''
                        })
                options['recent_commits'] = commits
            
            # Get recent operations
            if os.path.exists(self.operations_log_file):
                with open(self.operations_log_file, 'r') as f:
                    operations = json.load(f)
                    options['operations_history'] = operations[-10:]  # Last 10 operations
        
        except Exception as e:
            logger.error(f"Error getting rollback options: {e}")
        
        return options
    
    def cleanup_old_branches(self, days_to_keep: int = 7) -> Dict[str, int]:
        """
        Clean up old backup and agent branches.
        
        Args:
            days_to_keep: Number of days to keep branches
            
        Returns:
            Cleanup statistics
        """
        cutoff_timestamp = datetime.now(timezone.utc).timestamp() - (days_to_keep * 24 * 3600)
        
        stats = {
            'backup_branches_deleted': 0,
            'agent_branches_deleted': 0,
            'errors': 0
        }
        
        try:
            # Get all branches
            result = self._run_git_command(['branch', '--list'])
            if result.returncode != 0:
                return stats
            
            branches = [b.strip().replace('* ', '') for b in result.stdout.split('\n') if b.strip()]
            
            for branch in branches:
                try:
                    # Skip main branches
                    if branch in ['main', 'master'] or branch == self.get_current_branch():
                        continue
                    
                    # Parse branch timestamp for agent/backup branches
                    timestamp_match = None
                    if branch.startswith('backup-') or branch.startswith('agent-'):
                        timestamp_match = re.search(r'(\d{8}_\d{6})', branch)
                    
                    if timestamp_match:
                        branch_timestamp_str = timestamp_match.group(1)
                        branch_timestamp = datetime.strptime(branch_timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if branch_timestamp.timestamp() < cutoff_timestamp:
                            # Delete old branch
                            result = self._run_git_command(['branch', '-D', branch])
                            if result.returncode == 0:
                                if branch.startswith('backup-'):
                                    stats['backup_branches_deleted'] += 1
                                else:
                                    stats['agent_branches_deleted'] += 1
                                logger.info(f"Deleted old branch: {branch}")
                            else:
                                stats['errors'] += 1
                                logger.warning(f"Failed to delete branch {branch}: {result.stderr}")
                
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Error processing branch {branch}: {e}")
        
        except Exception as e:
            logger.error(f"Error during branch cleanup: {e}")
            stats['errors'] += 1
        
        logger.info(f"Branch cleanup completed: {stats}")
        return stats
    
    def get_safety_status(self) -> Dict[str, Any]:
        """
        Get safety status of the repository.
        
        Returns:
            Safety status information
        """
        status = {
            'repo_path': self.repo_path,
            'current_branch': self.get_current_branch(),
            'current_commit': self.get_current_commit(),
            'is_safe_branch': False,
            'has_uncommitted_changes': False,
            'backup_branches_available': 0,
            'recent_operations_count': 0,
            'git_hooks_installed': False,
            'recommendations': []
        }
        
        try:
            current_branch = status['current_branch']
            
            # Check if on safe branch
            status['is_safe_branch'] = (
                current_branch.startswith('agent-') or 
                current_branch.startswith('backup-') or
                current_branch not in ['main', 'master']
            )
            
            # Check for uncommitted changes
            result = self._run_git_command(['status', '--porcelain'])
            status['has_uncommitted_changes'] = bool(result.stdout.strip())
            
            # Count backup branches
            result = self._run_git_command(['branch', '--list', 'backup-*'])
            if result.returncode == 0:
                status['backup_branches_available'] = len([b for b in result.stdout.split('\n') if b.strip()])
            
            # Count recent operations
            if os.path.exists(self.operations_log_file):
                with open(self.operations_log_file, 'r') as f:
                    operations = json.load(f)
                    status['recent_operations_count'] = len(operations)
            
            # Check git hooks
            pre_commit_hook = os.path.join(self.repo_path, '.git', 'hooks', 'pre-commit')
            status['git_hooks_installed'] = os.path.exists(pre_commit_hook)
            
            # Generate recommendations
            recommendations = []
            
            if not status['is_safe_branch']:
                recommendations.append("Consider switching to a feature branch before making changes")
            
            if status['has_uncommitted_changes']:
                recommendations.append("Commit or stash uncommitted changes before major operations")
            
            if status['backup_branches_available'] == 0:
                recommendations.append("Create backup branch before starting agent work")
            
            if not status['git_hooks_installed']:
                recommendations.append("Reinstall git hooks for additional safety")
            
            status['recommendations'] = recommendations
        
        except Exception as e:
            logger.error(f"Error getting safety status: {e}")
            status['error'] = str(e)
        
        return status


# Global instance
_safe_git_operations: Optional[SafeGitOperations] = None


def get_safe_git_operations(repo_path: str = ".") -> SafeGitOperations:
    """Get global safe git operations instance."""
    global _safe_git_operations
    
    if _safe_git_operations is None:
        _safe_git_operations = SafeGitOperations(repo_path)
    
    return _safe_git_operations


if __name__ == "__main__":
    # Test safe git operations
    try:
        print("Testing SafeGitOperations...")
        
        # Create test repo in temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_repo = os.path.join(temp_dir, 'test_repo')
            os.makedirs(test_repo)
            
            # Initialize git repo
            subprocess.run(['git', 'init'], cwd=test_repo, check=True)
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=test_repo, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=test_repo, check=True)
            
            # Create initial commit
            test_file = os.path.join(test_repo, 'README.md')
            with open(test_file, 'w') as f:
                f.write('# Test Repository')
            
            subprocess.run(['git', 'add', '.'], cwd=test_repo, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=test_repo, check=True)
            
            # Test SafeGitOperations
            safe_git = SafeGitOperations(test_repo)
            print(f"✓ Initialized SafeGitOperations for: {test_repo}")
            
            # Test branch creation
            agent_branch, backup_branch = safe_git.create_agent_branch("TestAgent", "Testing git operations")
            print(f"✓ Created branches: {agent_branch}, {backup_branch}")
            
            # Test atomic commit
            with open(test_file, 'a') as f:
                f.write('\nTest modification')
            
            operation = safe_git.atomic_commit("TestAgent", "Test modification")
            print(f"✓ Atomic commit: {operation.status.value}")
            
            # Test rollback options
            options = safe_git.get_rollback_options()
            print(f"✓ Rollback options: {len(options['backup_branches'])} backups, {len(options['recent_commits'])} commits")
            
            # Test safety status
            status = safe_git.get_safety_status()
            print(f"✓ Safety status: safe_branch={status['is_safe_branch']}, recommendations={len(status['recommendations'])}")
            
            print("\n✅ All SafeGitOperations tests passed!")
    
    except Exception as e:
        print(f"❌ SafeGitOperations test failed: {e}")
        raise