"""
Testing Agent

Monitors PRs for automated testing and quality assurance.
Runs comprehensive test suites and reports results to Discord.
"""

import asyncio
import logging
import os
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import dependencies with error handling
try:
    from agents.backend.github_client import GitHubClient
except ImportError:
    GitHubClient = None
    logger = None  # Will be set below

try:
    from agents.backend.orchestrator_client import OrchestratorClient
except ImportError:
    OrchestratorClient = None

from agents.testing.test_runner import TestRunner

import logging
logger = logging.getLogger(__name__)

class TestingAgent:
    """
    Automated testing agent that monitors PRs and runs comprehensive tests.
    
    Features:
    - PR monitoring and automated testing
    - Comprehensive test suite execution
    - Security scans and code quality checks
    - Discord notifications for test results
    - Automatic PR approval for passing tests
    """
    
    def __init__(self):
        """Initialize the testing agent."""
        self.github_client = GitHubClient()
        self.orchestrator_client = OrchestratorClient()
        self.test_runner = TestRunner()
        
        # Configuration
        self.polling_interval = int(os.getenv('TESTING_POLLING_INTERVAL', '60'))  # seconds
        self.auto_approve = os.getenv('TESTING_AUTO_APPROVE', 'true').lower() == 'true'
        self.workspace_dir = Path('/tmp/testing_workspace')
        
        # State tracking
        self.tested_commits = set()
        self.running_tests = {}  # pr_number -> test_task
        
        logger.info(f"Testing Agent initialized - Auto approve: {self.auto_approve}")
    
    async def start(self):
        """Start the testing agent main loop."""
        logger.info("Testing Agent starting...")
        
        # Ensure workspace directory exists
        self.workspace_dir.mkdir(exist_ok=True)
        
        # Notify orchestrator that testing agent is online
        await self._notify_agent_status("online")
        
        try:
            while True:
                await self._monitoring_cycle()
                await asyncio.sleep(self.polling_interval)
                
        except Exception as e:
            logger.error(f"Testing Agent main loop failed: {e}")
            await self._notify_agent_status("error", str(e))
            raise
        finally:
            await self._notify_agent_status("offline")
    
    async def _monitoring_cycle(self):
        """Single monitoring cycle - check for new PRs and run tests."""
        try:
            # Log monitoring activity every 10 cycles (10 minutes by default)
            if not hasattr(self, '_cycle_count'):
                self._cycle_count = 0
            
            self._cycle_count += 1
            if self._cycle_count % 10 == 0:
                logger.info(f"Testing Agent monitoring pulse - Cycle {self._cycle_count} | Active tests: {len(self.running_tests)} | Tested commits: {len(self.tested_commits)}")
            
            # Get open PRs
            prs = await self.github_client.list_pull_requests()
            
            # Log PR discovery
            if prs:
                logger.debug(f"Found {len(prs)} open PRs to evaluate")
            
            for pr in prs:
                pr_number = pr['number']
                commit_sha = pr['head']['sha']
                
                # Skip if already tested this commit
                test_key = f"{pr_number}:{commit_sha}"
                if test_key in self.tested_commits:
                    continue
                
                # Skip if tests are already running
                if pr_number in self.running_tests:
                    continue
                
                # Skip draft PRs
                if pr.get('draft', False):
                    logger.info(f"Skipping draft PR #{pr_number}")
                    continue
                
                # Check if PR was created by an agent
                if await self._is_agent_pr(pr):
                    logger.info(f"🧪 Detected new agent PR #{pr_number} - '{pr['title']}' by {pr['user']['login']}")
                    await self._run_pr_tests(pr)
                    self.tested_commits.add(test_key)
                
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    async def _is_agent_pr(self, pr: Dict) -> bool:
        """Check if PR was created by an agent."""
        author = pr['user']['login']
        
        # Check for agent indicators
        agent_indicators = [
            'backend-agent',
            'testing-agent', 
            'orchestrator',
            '[AGENT]',
            '[BOT]'
        ]
        
        # Check username and title
        title = pr['title'].lower()
        author_lower = author.lower()
        
        return any(indicator.lower() in author_lower or indicator.lower() in title 
                  for indicator in agent_indicators)
    
    async def _run_pr_tests(self, pr: Dict):
        """Run comprehensive tests on a PR."""
        pr_number = pr['number']
        
        try:
            # Notify that tests are starting
            await self._notify_test_start(pr)
            
            # Create test task
            task = asyncio.create_task(self._execute_pr_tests(pr))
            self.running_tests[pr_number] = task
            
            # Wait for completion
            await task
            
        except Exception as e:
            logger.error(f"Error running tests for PR #{pr_number}: {e}")
            await self._report_test_failure(pr, str(e))
        finally:
            # Clean up
            self.running_tests.pop(pr_number, None)
    
    async def _execute_pr_tests(self, pr: Dict):
        """Execute the full test suite for a PR."""
        pr_number = pr['number']
        branch_name = pr['head']['ref']
        repo_url = pr['head']['repo']['clone_url']
        
        logger.info(f"Running tests for PR #{pr_number} - {pr['title']}")
        
        # Create temporary workspace
        test_workspace = self.workspace_dir / f"pr_{pr_number}"
        
        try:
            # Clone repository and checkout PR branch
            await self._setup_test_workspace(test_workspace, repo_url, branch_name)
            
            # Run comprehensive test suite
            test_results = await self.test_runner.run_comprehensive_tests(test_workspace)
            
            # Report results
            await self._report_test_results(pr, test_results)
            
            # Auto-approve if all tests pass
            if self.auto_approve and test_results['overall_status'] == 'pass':
                await self._auto_approve_pr(pr, test_results)
            
        finally:
            # Clean up workspace
            if test_workspace.exists():
                shutil.rmtree(test_workspace, ignore_errors=True)
    
    async def _setup_test_workspace(self, workspace: Path, repo_url: str, branch: str):
        """Set up test workspace with PR branch."""
        logger.info(f"Setting up test workspace: {workspace}")
        
        # Remove existing workspace
        if workspace.exists():
            shutil.rmtree(workspace)
        
        # Clone repository
        clone_cmd = f"git clone {repo_url} {workspace}"
        process = await asyncio.create_subprocess_shell(
            clone_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Failed to clone repository: {repo_url}")
        
        # Checkout PR branch
        checkout_cmd = f"cd {workspace} && git checkout {branch}"
        process = await asyncio.create_subprocess_shell(
            checkout_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Failed to checkout branch: {branch}")
        
        logger.info(f"Test workspace ready: {workspace}")
    
    async def _report_test_results(self, pr: Dict, test_results: Dict):
        """Report test results to Discord."""
        pr_number = pr['number']
        
        # Format test results for Discord
        message = self._format_test_results_message(pr, test_results)
        
        # Send to orchestrator for Discord notification
        await self.orchestrator_client.send_notification(
            channel="testing",
            message=message,
            priority="normal" if test_results['overall_status'] == 'pass' else "high"
        )
        
        logger.info(f"Test results reported for PR #{pr_number}: {test_results['overall_status']}")
    
    def _format_test_results_message(self, pr: Dict, results: Dict) -> str:
        """Format test results into Discord message."""
        pr_number = pr['number']
        title = pr['title']
        status = results['overall_status']
        
        # Status emoji
        status_emoji = "✅" if status == 'pass' else "❌"
        
        message = f"""
🧪 **Test Results - PR #{pr_number}**
{status_emoji} **Status:** {status.upper()}

📋 **PR:** {title}
👤 **Author:** {pr['user']['login']}
🌿 **Branch:** {pr['head']['ref']}

**📊 Test Summary:**
"""
        
        # Add test category results
        for category, result in results.get('categories', {}).items():
            emoji = "✅" if result['status'] == 'pass' else "❌"
            message += f"{emoji} **{category.title()}:** {result['status']} ({result.get('score', 'N/A')})\n"
        
        # Add details for failed tests
        if status != 'pass':
            message += "\n**🔍 Failed Tests:**\n"
            for category, result in results.get('categories', {}).items():
                if result['status'] != 'pass':
                    message += f"• {category}: {result.get('details', 'No details')}\n"
        
        # Add coverage info
        coverage = results.get('coverage', {})
        if coverage:
            message += f"\n📈 **Coverage:** {coverage.get('percentage', 'N/A')}%"
        
        # Add performance metrics
        duration = results.get('duration', 0)
        message += f"\n⏱️ **Duration:** {duration:.1f}s"
        
        return message.strip()
    
    async def _notify_test_start(self, pr: Dict):
        """Notify that tests are starting on a PR."""
        pr_number = pr['number']
        
        message = f"""
🧪 **Starting Tests - PR #{pr_number}**

📋 **PR:** {pr['title']}
👤 **Author:** {pr['user']['login']}
🌿 **Branch:** {pr['head']['ref']}

🔄 Running comprehensive test suite...
⏱️ Expected duration: ~1-2 minutes
"""
        
        await self.orchestrator_client.send_notification(
            channel="testing",
            message=message,
            priority="low"
        )
    
    async def _report_test_failure(self, pr: Dict, error: str):
        """Report test execution failure."""
        pr_number = pr['number']
        
        message = f"""
🚨 **Test Execution Failed - PR #{pr_number}**

📋 **PR:** {pr['title']}
👤 **Author:** {pr['user']['login']}

❌ **Error:** {error}

Please check the testing agent logs for more details.
Use `/test-logs` to view recent activity.
"""
        
        await self.orchestrator_client.send_notification(
            channel="testing",
            message=message,
            priority="high"
        )
    
    async def _auto_approve_pr(self, pr: Dict, test_results: Dict):
        """Automatically approve PR if all tests pass."""
        pr_number = pr['number']
        
        try:
            # Approve the PR
            await self.github_client.approve_pull_request(
                pr_number, 
                "✅ Automated approval - All tests passed"
            )
            
            # Notify about auto-approval
            message = f"""
🤖 **Auto-Approved PR #{pr_number}**

✅ All tests passed - PR automatically approved!

🔄 Ready for merge when human review is complete.
"""
            
            await self.orchestrator_client.send_notification(
                channel="testing",
                message=message,
                priority="normal"
            )
            
            logger.info(f"Auto-approved PR #{pr_number}")
            
        except Exception as e:
            logger.error(f"Failed to auto-approve PR #{pr_number}: {e}")
    
    async def _notify_agent_status(self, status: str, details: Optional[str] = None):
        """Notify orchestrator about agent status."""
        try:
            if status == "online":
                message = f"""🧪 **Testing Agent Started!**

✅ **Status:** Online and monitoring
🔄 **Monitoring:** Checking PRs every {self.polling_interval}s  
🤖 **Auto-Approve:** {'Enabled' if self.auto_approve else 'Disabled'}
📁 **Workspace:** {self.workspace_dir}

Ready to test PRs automatically! Use `/test-status` for details."""
            elif status == "offline":
                message = f"🧪 **Testing Agent:** Stopped"
            else:
                message = f"🧪 Testing Agent: {status.upper()}"
                if details:
                    message += f"\nDetails: {details}"
            
            await self.orchestrator_client.send_notification(
                channel="system",
                message=message,
                priority="normal" if status == "online" else "low"
            )
        except Exception as e:
            logger.error(f"Failed to notify agent status: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current testing agent status."""
        return {
            "agent": "testing",
            "status": "running",
            "active_tests": len(self.running_tests),
            "tested_commits": len(self.tested_commits),
            "auto_approve": self.auto_approve,
            "workspace": str(self.workspace_dir),
            "polling_interval": self.polling_interval
        }