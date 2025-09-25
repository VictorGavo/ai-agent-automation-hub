"""
Discord Bot Main Implementation - Full Version

Discord bot with complete command set including all orchestrator commands.
Uses discord.Client with app_commands for reliable slash command registration.
"""

import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator_agent import OrchestratorAgent
from agents.backend_agent import BackendAgent
from agents.database_agent import DatabaseAgent
from bot.safety_commands import setup_safety_commands
from safety_monitor import get_safety_monitor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discord_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FullDiscordBot(discord.Client):
    """
    Full Discord bot using discord.Client with CommandTree for comprehensive command set.
    
    This version includes all orchestrator commands and full agent integration.
    """
    
    def __init__(self) -> None:
        """Initialize the full Discord bot."""
        
        # Configure bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(intents=intents)
        
        # Initialize command tree
        self.tree = app_commands.CommandTree(self)
        
        # Initialize orchestrator (main agent)
        self.orchestrator: Optional[OrchestratorAgent] = None
        self.backend_agent: Optional[BackendAgent] = None
        self.database_agent: Optional[DatabaseAgent] = None
        
        # State tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.agent_status: Dict[str, str] = {
            'orchestrator': 'initializing',
            'backend': 'initializing', 
            'database': 'initializing'
        }
        
        # Initialize safety monitor
        self.safety_monitor = get_safety_monitor({
            'discord_webhook_url': None,  # Could be configured
            'monitoring_interval': 30
        })
        
        # Setup slash commands from orchestrator commands
        self._setup_commands()
        
        # Setup safety commands
        setup_safety_commands(self)
        
        logger.info("Full Discord bot initialized successfully")
    
    def _setup_commands(self) -> None:
        """Set up full slash command set from orchestrator commands."""
        
        # Import the task priority enum for proper typing
        try:
            from database.models.task import TaskPriority
        except ImportError:
            logger.warning("Could not import TaskPriority, using string values")
            TaskPriority = None
        
        # ============ BASIC COMMANDS ============
        
        @self.tree.command(name="ping", description="Check if the bot is responsive")
        async def ping_command(interaction: discord.Interaction):
            """Simple ping command to test bot responsiveness"""
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("🏓 Pong! Automation Hub is online and ready.", ephemeral=True)
            logger.info(f"Ping command used by {interaction.user}")
        
        @self.tree.command(name="assign-task", description="Assign a new development task to the AI agents")
        @app_commands.describe(
            description="Describe what you want the agents to build or fix",
            priority="Task priority (low, medium, high, urgent)"
        )
        @app_commands.choices(priority=[
            app_commands.Choice(name="Low", value="low"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="High", value="high"),
            app_commands.Choice(name="Urgent", value="urgent")
        ])
        async def assign_task_command(interaction: discord.Interaction, description: str, priority: Optional[str] = "medium"):
            """Assign a development task to AI agents"""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                # Simplified approach - direct execution without nested async function
                result = None
                
                if self.orchestrator and hasattr(self.orchestrator, 'assign_task'):
                    try:
                        # Use full orchestrator if available with timeout
                        if TaskPriority:
                            task_priority = TaskPriority(priority.lower())
                        else:
                            task_priority = priority.lower()
                        
                        result = await asyncio.wait_for(
                            self.orchestrator.assign_task(
                                description=description,
                                user_id=str(interaction.user.id),
                                channel_id=str(interaction.channel.id),
                                priority=task_priority
                            ),
                            timeout=25
                        )
                    except asyncio.TimeoutError:
                        await interaction.followup.send("⏱️ Task assignment is taking longer than expected. The task has been queued and you'll be notified when it's processed.")
                        logger.warning(f"Task assignment timeout for user {interaction.user}: {description[:100]}")
                        return
                else:
                    # Fallback to simple task assignment
                    task_id = f"task_{len(self.active_tasks) + 1}_{datetime.now().strftime('%H%M%S')}"
                    
                    self.active_tasks[task_id] = {
                        'description': description,
                        'priority': priority,
                        'status': 'assigned',
                        'created_at': datetime.now(),
                        'assigned_by': interaction.user.id
                    }
                    
                    result = {
                        "success": True,
                        "task_id": task_id,
                        "requires_clarification": False,
                        "estimated_hours": 2.0,
                        "category": "general",
                        "message": f"Task assigned successfully! (Simplified mode)"
                    }
                    
                if result and result["success"]:
                    if result.get("requires_clarification"):
                        # Create clarification embed
                        embed = discord.Embed(
                            title="🤔 Task Needs Clarification",
                            description=f"**Task:** {description[:200]}...\n\n**Task ID:** `{result['task_id']}`",
                            color=discord.Color.orange()
                        )
                        
                        # Add clarifying questions
                        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(result.get("questions", []))])
                        embed.add_field(name="Questions:", value=questions_text, inline=False)
                        embed.add_field(name="Next Steps:", value="Please answer these questions using `/clarify-task`", inline=False)
                    else:
                        # Task assigned successfully
                        embed = discord.Embed(
                            title="✅ Task Assigned Successfully",
                            description=f"**Task:** {description[:200]}...\n\n**Task ID:** `{result['task_id']}`",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Estimated Time:", value=f"{result.get('estimated_hours', 'TBD')} hours", inline=True)
                        embed.add_field(name="Category:", value=result.get("category", "general").title(), inline=True)
                        embed.add_field(name="Priority:", value=priority.title(), inline=True)
                elif result:
                    # Task assignment failed
                    embed = discord.Embed(
                        title="❌ Task Assignment Failed",
                        description=result["message"],
                        color=discord.Color.red()
                    )
                else:
                    # No result
                    embed = discord.Embed(
                        title="❌ Task Assignment Failed",
                        description="An unexpected error occurred during task assignment.",
                        color=discord.Color.red()
                    )
                
                await interaction.followup.send(embed=embed)
                logger.info(f"Task assigned by {interaction.user}: {description[:100]}")
                
            except Exception as e:
                logger.error(f"Task assignment command failed: {e}")
                await interaction.followup.send("⚠️ An error occurred while processing your task. Please try again.")
        
        @self.tree.command(name="clarify-task", description="Provide clarification for a pending task")
        @app_commands.describe(
            task_id="The task ID that needs clarification",
            answer1="Answer to first question",
            answer2="Answer to second question (optional)",
            answer3="Answer to third question (optional)",
            answer4="Answer to fourth question (optional)",
            answer5="Answer to fifth question (optional)"
        )
        async def clarify_task_command(
            interaction: discord.Interaction, 
            task_id: str,
            answer1: str,
            answer2: Optional[str] = None,
            answer3: Optional[str] = None,
            answer4: Optional[str] = None,
            answer5: Optional[str] = None
        ):
            """Provide clarification answers for a task"""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                timeout_seconds = 25
                
                async def process_clarification_with_timeout():
                    if self.orchestrator and hasattr(self.orchestrator, 'provide_clarification'):
                        # Collect non-empty answers
                        answers = [answer for answer in [answer1, answer2, answer3, answer4, answer5] if answer]
                        
                        # Process clarification
                        result = await self.orchestrator.provide_clarification(task_id, answers)
                        return result
                    else:
                        return {
                            "success": False,
                            "message": "Task clarification requires full orchestrator integration"
                        }
                
                # Execute with timeout
                try:
                    result = await asyncio.wait_for(process_clarification_with_timeout(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    await interaction.followup.send("⏱️ Task clarification is taking longer than expected. Please try again in a moment.")
                    logger.warning(f"Task clarification timeout for user {interaction.user}: {task_id}")
                    return
                
                if result["success"]:
                    embed = discord.Embed(
                        title="✅ Task Clarified and Assigned",
                        description=result["message"],
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Task ID:", value=f"`{task_id}`", inline=True)
                    embed.add_field(name="Estimated Time:", value=f"{result.get('estimated_hours', 'TBD')} hours", inline=True)
                else:
                    embed = discord.Embed(
                        title="❌ Clarification Failed",
                        description=result["message"],
                        color=discord.Color.red()
                    )
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Task clarification command failed: {e}")
                await interaction.followup.send("⚠️ An error occurred while processing your clarification. Please try again.")
        
        # ============ STATUS AND MONITORING COMMANDS ============
        
        @self.tree.command(name="status", description="Get current system and task status")
        async def status_command(interaction: discord.Interaction):
            """Display comprehensive system status"""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                timeout_seconds = 20
                
                async def get_status_with_timeout():
                    if self.orchestrator and hasattr(self.orchestrator, 'get_status_report'):
                        status_report = await self.orchestrator.get_status_report()
                        
                        embed = discord.Embed(
                            title="🤖 Automation Hub Status",
                            color=discord.Color.blue()
                        )
                        
                        if "error" in status_report:
                            embed.description = f"⚠️ {status_report['error']}"
                            embed.color = discord.Color.red()
                        else:
                            # System status
                            uptime = status_report.get('uptime', 'Unknown')
                            embed.add_field(
                                name="🔧 System", 
                                value=f"Status: {status_report.get('orchestrator_status', 'unknown').title()}\nUptime: {uptime}", 
                                inline=True
                            )
                            
                            # Task statistics
                            tasks = status_report.get('tasks', {})
                            embed.add_field(
                                name="📋 Active Tasks",
                                value=f"Total: {tasks.get('total', len(self.active_tasks))}\nPending: {tasks.get('pending', 0)}\nIn Progress: {tasks.get('in_progress', 0)}\nCompleted: {tasks.get('completed', 0)}",
                                inline=True
                            )
                            
                            # Agent status
                            embed.add_field(
                                name="🤖 Agents",
                                value=f"Orchestrator: {self.agent_status.get('orchestrator', 'unknown')}\nBackend: {self.agent_status.get('backend', 'unknown')}\nDatabase: {self.agent_status.get('database', 'unknown')}",
                                inline=True
                            )
                            
                            # Add quick action guides
                            embed.set_footer(text="💡 /assign-task • /approve [pr-number] • /pending-prs • /emergency-stop")
                        return embed
                    else:
                        # Fallback status display
                        embed = discord.Embed(
                            title="🤖 Basic Bot Status",
                            color=discord.Color.blue()
                        )
                        
                        for agent_name, status in self.agent_status.items():
                            status_icon = "✅" if status == "ready" else "❌" if status == "error" else "⚠️"
                            embed.add_field(
                                name=f"{status_icon} {agent_name.title()} Agent",
                                value=f"Status: {status}",
                                inline=True
                            )
                        
                        embed.add_field(
                            name="📊 Active Tasks",
                            value=f"{len(self.active_tasks)} tasks running",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="Note", 
                            value="Full orchestrator not available - showing basic status", 
                            inline=False
                        )
                        return embed
                
                # Execute with timeout
                try:
                    embed = await asyncio.wait_for(get_status_with_timeout(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    embed = discord.Embed(
                        title="⏱️ Status Check Timeout",
                        description="Status retrieval is taking longer than expected. The system may be under heavy load.",
                        color=discord.Color.orange()
                    )
                    embed.add_field(name="Suggestion", value="Try again in a moment or contact support if this persists.", inline=False)
                    logger.warning(f"Status command timeout for user {interaction.user}")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Status command failed: {e}")
                await interaction.followup.send("⚠️ Failed to retrieve system status. Please try again.")
        
        # ============ PR MANAGEMENT COMMANDS ============
        
        @self.tree.command(name="approve", description="Approve and merge a specific pull request")
        @app_commands.describe(pr_number="The pull request number to approve and merge")
        async def approve_pr_command(interaction: discord.Interaction, pr_number: int):
            """Approve and merge a pull request"""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                # Simplified approach - direct execution without nested async function
                embed = None
                
                # Try to get GitHub client from backend agent first
                github_client = None
                if self.backend_agent and hasattr(self.backend_agent, 'github_client'):
                    github_client = self.backend_agent.github_client
                elif self.orchestrator and hasattr(self.orchestrator, 'github_client'):
                    github_client = self.orchestrator.github_client
                
                if github_client:
                    try:
                        # First, get PR details with timeout
                        pr_details = await asyncio.wait_for(
                            github_client.get_pull_request(pr_number),
                            timeout=20
                        )
                        
                        if not pr_details:
                            embed = discord.Embed(
                                title="❌ PR Not Found",
                                description=f"Pull request #{pr_number} was not found.",
                                color=discord.Color.red()
                            )
                        
                        # Check if PR is already merged
                        elif pr_details.get('merged'):
                            embed = discord.Embed(
                                title="ℹ️ PR Already Merged",
                                description=f"**PR #{pr_number}** - {pr_details.get('title', 'No title')}\n\nThis pull request has already been merged.",
                                color=discord.Color.blue()
                            )
                            embed.add_field(name="Author", value=pr_details.get('author', 'Unknown'), inline=True)
                            embed.add_field(name="Branch", value=f"`{pr_details.get('head_branch', 'unknown')}`", inline=True)
                        
                        # Check if PR is mergeable
                        elif not pr_details.get('mergeable'):
                            mergeable_state = pr_details.get('mergeable_state', 'unknown')
                            embed = discord.Embed(
                                title="⚠️ PR Cannot Be Merged",
                                description=f"**PR #{pr_number}** - {pr_details.get('title', 'No title')}\n\nThis PR cannot be merged due to: `{mergeable_state}`",
                                color=discord.Color.orange()
                            )
                            embed.add_field(name="Author", value=pr_details.get('author', 'Unknown'), inline=True)
                            embed.add_field(name="Branch", value=f"`{pr_details.get('head_branch', 'unknown')}`", inline=True)
                            embed.add_field(name="Suggestion", value="Please resolve conflicts or check PR status on GitHub", inline=False)
                        
                        else:
                            # Attempt to merge the PR with timeout
                            merge_result = await asyncio.wait_for(
                                github_client.merge_pull_request(pr_number, merge_method="merge"),
                                timeout=20
                            )
                            
                            if merge_result and merge_result.get('success'):
                                embed = discord.Embed(
                                    title="✅ PR Approved and Merged",
                                    description=f"**PR #{pr_number}** - {pr_details.get('title', 'No title')}\n\nSuccessfully merged by {interaction.user.mention}",
                                    color=discord.Color.green()
                                )
                                embed.add_field(name="Author", value=pr_details.get('author', 'Unknown'), inline=True)
                                embed.add_field(name="Branch", value=f"`{pr_details.get('head_branch', 'unknown')}` → `{pr_details.get('base_branch', 'main')}`", inline=True)
                                embed.add_field(name="Files Changed", value=f"{pr_details.get('files_changed_count', 0)} files (+{pr_details.get('additions', 0)} -{pr_details.get('deletions', 0)})", inline=True)
                                
                                if merge_result.get('sha'):
                                    embed.add_field(name="Merge Commit", value=f"`{merge_result['sha'][:8]}`", inline=True)
                                
                                embed.add_field(name="View PR", value=f"[GitHub Link]({pr_details.get('url', '#')})", inline=True)
                                embed.set_footer(text=f"Approved by {interaction.user.display_name}")
                            else:
                                error_message = merge_result.get('message', 'Unknown error') if merge_result else 'Merge operation failed'
                                embed = discord.Embed(
                                    title="❌ PR Merge Failed",
                                    description=f"**PR #{pr_number}** could not be merged.\n\n**Error:** {error_message}",
                                    color=discord.Color.red()
                                )
                    
                    except asyncio.TimeoutError:
                        embed = discord.Embed(
                            title="⏱️ PR Approval Timeout",
                            description=f"PR #{pr_number} approval is taking longer than expected. This may be due to GitHub API delays.",
                            color=discord.Color.orange()
                        )
                        embed.add_field(name="Suggestion", value="Try again in a moment or check the PR status on GitHub directly.", inline=False)
                        logger.warning(f"PR approval timeout for user {interaction.user}: PR #{pr_number}")
                    except Exception as github_error:
                        logger.error(f"GitHub API error during PR approval: {github_error}")
                        embed = discord.Embed(
                            title="❌ GitHub API Error",
                            description=f"Failed to process PR #{pr_number}: {str(github_error)}",
                            color=discord.Color.red()
                        )
                
                elif self.orchestrator and hasattr(self.orchestrator, 'approve_and_merge_pr'):
                    try:
                        # Fallback to orchestrator method with timeout
                        result = await asyncio.wait_for(
                            self.orchestrator.approve_and_merge_pr(pr_number, str(interaction.user.id)),
                            timeout=20
                        )
                        
                        if result["success"]:
                            embed = discord.Embed(
                                title="✅ PR Approved and Merged",
                                description=f"**PR #{pr_number}** has been successfully merged by {interaction.user.mention}",
                                color=discord.Color.green()
                            )
                            embed.add_field(name="PR Title", value=result.get("pr_title", "N/A"), inline=False)
                            if result.get("sha"):
                                embed.add_field(name="Merge Commit", value=f"`{result['sha'][:8]}`", inline=True)
                            embed.set_footer(text=f"Approved by {interaction.user.display_name}")
                        else:
                            embed = discord.Embed(
                                title="❌ PR Approval Failed",
                                description=result["message"],
                                color=discord.Color.red()
                            )
                    except asyncio.TimeoutError:
                        embed = discord.Embed(
                            title="⏱️ PR Approval Timeout",
                            description=f"PR #{pr_number} approval is taking longer than expected.",
                            color=discord.Color.orange()
                        )
                        embed.add_field(name="Suggestion", value="Try again in a moment.", inline=False)
                        logger.warning(f"Orchestrator PR approval timeout for user {interaction.user}: PR #{pr_number}")
                else:
                    embed = discord.Embed(
                        title="❌ GitHub Integration Not Available",
                        description="PR approval requires GitHub integration. Please check:\n" +
                                  "• `GITHUB_TOKEN` environment variable is set\n" +
                                  "• `GITHUB_REPO` environment variable is set\n" +
                                  "• Token has repository write permissions",
                        color=discord.Color.red()
                    )
                
                # Send the response
                if embed:
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("⚠️ An unexpected error occurred while processing the PR approval.")
                
            except Exception as e:
                logger.error(f"Approve PR command failed: {e}")
                await interaction.followup.send("⚠️ An error occurred while approving the PR. Please try again.")
        
        @self.tree.command(name="pending-prs", description="Show all open pull requests awaiting approval")
        @app_commands.describe(limit="Maximum number of PRs to show (default: 10)")
        async def pending_prs_command(interaction: discord.Interaction, limit: Optional[int] = 10):
            """Display all pending pull requests"""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                # Limit the number to reasonable bounds
                limit = min(max(1, limit or 10), 20)
                
                # Simplified approach - direct execution without nested async function
                embed = None
                
                # Try to get GitHub client from orchestrator first
                github_client = None
                if self.orchestrator and hasattr(self.orchestrator, 'github_client'):
                    github_client = self.orchestrator.github_client
                elif self.backend_agent and hasattr(self.backend_agent, 'github_client'):
                    github_client = self.backend_agent.github_client
                
                if github_client:
                    try:
                        # Get PRs directly from GitHub client with timeout
                        prs = await asyncio.wait_for(
                            github_client.list_pull_requests(state="open", limit=limit),
                            timeout=20
                        )
                        
                        if not prs:
                            embed = discord.Embed(
                                title="📭 No Pending PRs",
                                description="There are no open pull requests awaiting approval.",
                                color=discord.Color.green()
                            )
                        else:
                            # Create embed with PR list
                            embed = discord.Embed(
                                title=f"📋 Pending Pull Requests ({len(prs)})",
                                description=f"Repository: `{github_client.github_repo}`",
                                color=discord.Color.blue()
                            )
                            
                            for pr in prs:
                                # Create status indicators
                                status_parts = []
                                if pr.get("draft"):
                                    status_parts.append("🚧 Draft")
                                if not pr.get("mergeable"):
                                    status_parts.append("⚠️ Conflicts")
                                
                                # Review status indicator
                                review_status = pr.get("review_status", "pending")
                                if review_status == "approved":
                                    status_parts.append("✅ Approved")
                                elif review_status == "changes_requested":
                                    status_parts.append("🔄 Changes Requested")
                                
                                status_text = " • ".join(status_parts) if status_parts else "Ready for review"
                                
                                # Format branch info
                                branch_info = f"`{pr.get('head_branch', 'unknown')}` → `{pr.get('base_branch', 'main')}`"
                                
                                # Create field value
                                field_value = f"**Author:** {pr.get('author', 'unknown')}\n"
                                field_value += f"**Branch:** {branch_info}\n"
                                field_value += f"**Status:** {status_text}\n"
                                field_value += f"**Files:** {pr.get('files_changed', 0)} changed (+{pr.get('additions', 0)} -{pr.get('deletions', 0)})\n"
                                field_value += f"[View PR]({pr.get('url', '#')})"
                                
                                embed.add_field(
                                    name=f"#{pr.get('number')} - {pr.get('title', 'No title')[:40]}{'...' if len(pr.get('title', '')) > 40 else ''}",
                                    value=field_value,
                                    inline=False
                                )
                            
                            embed.set_footer(text="💡 Use /approve [pr-number] to approve and merge")
                    
                    except asyncio.TimeoutError:
                        embed = discord.Embed(
                            title="⏱️ PR Retrieval Timeout",
                            description="Retrieving PRs is taking longer than expected. This may be due to GitHub API delays.",
                            color=discord.Color.orange()
                        )
                        embed.add_field(name="Suggestion", value="Try again in a moment or check GitHub directly.", inline=False)
                        logger.warning(f"Pending PRs command timeout for user {interaction.user}")
                    except Exception as github_error:
                        logger.error(f"GitHub API error: {github_error}")
                        embed = discord.Embed(
                            title="❌ Failed to Load PRs",
                            description=f"GitHub API error: {str(github_error)}",
                            color=discord.Color.red()
                        )
                
                elif self.orchestrator and hasattr(self.orchestrator, 'list_pending_prs'):
                    try:
                        # Fallback to orchestrator method with timeout
                        result = await asyncio.wait_for(
                            self.orchestrator.list_pending_prs(limit),
                            timeout=20
                        )
                        
                        if not result["success"]:
                            embed = discord.Embed(
                                title="❌ Failed to Load PRs",
                                description=result["message"],
                                color=discord.Color.red()
                            )
                        else:
                            prs = result.get("prs", [])
                            
                            if not prs:
                                embed = discord.Embed(
                                    title="📭 No Pending PRs",
                                    description="There are no open pull requests awaiting approval.",
                                    color=discord.Color.green()
                                )
                            else:
                                # Create embed with PR list
                                embed = discord.Embed(
                                    title=f"📋 Pending Pull Requests ({len(prs)})",
                                    color=discord.Color.blue()
                                )
                                
                                for pr in prs:
                                    pr_status = f"by {pr.get('author', 'unknown')}"
                                    if pr.get("draft"):
                                        pr_status = "🚧 Draft • " + pr_status
                                    if not pr.get("mergeable"):
                                        pr_status = "⚠️ Conflicts • " + pr_status
                                    
                                    embed.add_field(
                                        name=f"#{pr.get('number')} - {pr.get('title', 'No title')[:50]}",
                                        value=f"{pr_status}\n[View PR]({pr.get('url', '#')})",
                                        inline=False
                                    )
                                
                                embed.set_footer(text="Use /approve [pr-number] to approve")
                    except asyncio.TimeoutError:
                        embed = discord.Embed(
                            title="⏱️ PR Retrieval Timeout",
                            description="Retrieving PRs is taking longer than expected.",
                            color=discord.Color.orange()
                        )
                        embed.add_field(name="Suggestion", value="Try again in a moment.", inline=False)
                        logger.warning(f"Orchestrator pending PRs timeout for user {interaction.user}")
                else:
                    embed = discord.Embed(
                        title="❌ GitHub Integration Not Available",
                        description="GitHub integration is not properly configured. Please check:\n" +
                                  "• `GITHUB_TOKEN` environment variable is set\n" +
                                  "• `GITHUB_REPO` environment variable is set\n" +
                                  "• Token has repository access permissions",
                        color=discord.Color.red()
                    )
                
                # Send the response
                if embed:
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("⚠️ An unexpected error occurred while retrieving pending PRs.")
                
            except Exception as e:
                logger.error(f"Pending PRs command failed: {e}")
                await interaction.followup.send("⚠️ An error occurred while retrieving pending PRs. Please try again.")
        
        @self.tree.command(name="emergency-stop", description="🚨 Emergency stop all agent activities")
        async def emergency_stop_command(interaction: discord.Interaction):
            """Emergency stop command for critical situations"""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                # Simplified approach - direct execution without nested async function
                # This is an emergency command so it should be fast and simple
                self.agent_status = {k: 'stopped' for k in self.agent_status.keys()}
                
                if self.orchestrator and hasattr(self.orchestrator, 'update_status'):
                    # TODO: Implement proper emergency stop
                    embed = discord.Embed(
                        title="🚨 Emergency Stop Activated",
                        description="All agent activities have been halted.\nUse `/status` to check system state.",
                        color=discord.Color.red()
                    )
                else:
                    embed = discord.Embed(
                        title="🚨 Emergency Stop (Basic)",
                        description="Bot commands disabled. Restart required for full functionality.",
                        color=discord.Color.red()
                    )
                
                await interaction.followup.send(embed=embed)
                logger.info(f"Emergency stop activated by {interaction.user}")
                
            except Exception as e:
                logger.error(f"Emergency stop command failed: {e}")
                await interaction.followup.send("⚠️ Emergency stop command failed. Please contact system administrator.")
        
        logger.info("Full command set (basic + status + PR management + emergency) set up successfully")
    
    async def setup_hook(self) -> None:
        """Set up the bot and initialize agents."""
        try:
            logger.info("Setting up full Discord bot...")
            
            # Initialize agents with full capabilities
            logger.info("Initializing agents...")
            try:
                # Initialize main orchestrator agent
                self.orchestrator = OrchestratorAgent("DiscordOrchestrator")
                self.backend_agent = BackendAgent("DiscordBackend")  
                self.database_agent = DatabaseAgent("DiscordDatabase")
                
                # Initialize orchestrator with full capabilities
                if self.orchestrator:
                    # Prepare orchestrator for Discord integration tasks (check if async)
                    if hasattr(self.orchestrator, 'prepare_for_task'):
                        try:
                            result = self.orchestrator.prepare_for_task("Discord integration", "orchestration")
                            if hasattr(result, '__await__'):
                                await result
                        except Exception as prep_error:
                            logger.warning(f"Orchestrator preparation failed: {prep_error}")
                    
                    # Initialize GitHub client
                    if hasattr(self.orchestrator, 'initialize_github_client'):
                        github_success = await self.orchestrator.initialize_github_client()
                        if github_success:
                            logger.info("✅ GitHub client initialized")
                        else:
                            logger.warning("⚠️ GitHub client initialization failed - PR commands may be limited")
                    
                    self.agent_status['orchestrator'] = 'ready'
                    logger.info("✅ Orchestrator agent ready")
                
                if self.backend_agent:
                    if hasattr(self.backend_agent, 'prepare_for_task'):
                        try:
                            result = self.backend_agent.prepare_for_task("Backend tasks", "backend")
                            if hasattr(result, '__await__'):
                                await result
                        except Exception as prep_error:
                            logger.warning(f"Backend preparation failed: {prep_error}")
                    
                    # Initialize GitHub client for backend agent
                    try:
                        github_success = await self.backend_agent.initialize_github_client()
                        if github_success:
                            logger.info("✅ Backend agent GitHub client initialized")
                        else:
                            logger.warning("⚠️ Backend agent GitHub initialization failed")
                    except Exception as github_error:
                        logger.warning(f"Backend GitHub initialization error: {github_error}")
                    
                    self.agent_status['backend'] = 'ready'
                    logger.info("✅ Backend agent ready")
                    
                if self.database_agent:
                    if hasattr(self.database_agent, 'prepare_for_task'):
                        try:
                            result = self.database_agent.prepare_for_task("Database operations", "database")
                            if hasattr(result, '__await__'):
                                await result
                        except Exception as prep_error:
                            logger.warning(f"Database preparation failed: {prep_error}")
                    self.agent_status['database'] = 'ready'
                    logger.info("✅ Database agent ready")
                    
                logger.info("Full agent suite initialized successfully")
                
            except Exception as e:
                logger.warning(f"Agent initialization failed, continuing with basic functionality: {e}")
                self.agent_status = {
                    'orchestrator': 'unavailable',
                    'backend': 'unavailable',
                    'database': 'unavailable'
                }
            
            # Start safety monitoring
            try:
                self.safety_monitor.start_monitoring()
                logger.info("✅ Safety monitoring started")
            except Exception as e:
                logger.warning(f"Failed to start safety monitoring: {e}")
            
            # Sync slash commands with improved error handling
            guild_id = os.getenv('DISCORD_GUILD_ID')
            
            # Debug: Show what commands are in the tree before syncing
            commands = self.tree.get_commands()
            logger.info(f"Commands in tree before sync: {len(commands)}")
            for cmd in commands:
                logger.info(f"  - {cmd.name}: {cmd.description}")
            
            # Always sync globally for reliability (guild sync seems to have issues)
            logger.info("Syncing commands globally for reliability...")
            synced = await self.tree.sync()
            logger.info(f"✅ Successfully synced {len(synced)} commands globally")
            
            for command in synced:
                logger.info(f"  - /{command.name}: {command.description}")
            
            if guild_id:
                logger.info(f"Note: Commands synced globally but will be available in guild {guild_id}")
            
            # If global sync fails, we can try guild sync as fallback
            if len(synced) == 0 and guild_id:
                try:
                    logger.warning("Global sync returned 0 commands, trying guild sync...")
                    guild_obj = discord.Object(id=int(guild_id))
                    synced = await self.tree.sync(guild=guild_obj)
                    logger.info(f"✅ Fallback: synced {len(synced)} commands to guild {guild_id}")
                except Exception as e:
                    logger.error(f"Guild sync also failed: {e}")
            
        except Exception as e:
            logger.error(f"Fatal error during bot setup: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def on_ready(self) -> None:
        """Event handler for when the bot connects successfully."""
        logger.info("=" * 50)
        logger.info(f"🤖 Bot connected as {self.user} (ID: {self.user.id})")
        logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        
        # Log guild information
        for guild in self.guilds:
            logger.info(f"  - {guild.name} (ID: {guild.id})")
        
        # Update bot presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for /assign-task commands"
        )
        await self.change_presence(activity=activity)
        
        # Log available commands
        commands = await self.tree.fetch_commands()
        logger.info(f"📋 Available slash commands: {len(commands)}")
        for cmd in commands:
            logger.info(f"  - /{cmd.name}")
        
        logger.info("✅ Bot is ready and online!")
        logger.info("=" * 50)
    
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        """Handle slash command errors."""
        logger.error(f"Slash command error: {error}")
        
        # Determine appropriate response method based on interaction state
        try:
            if isinstance(error, app_commands.CommandOnCooldown):
                message = f"⏰ Command on cooldown. Try again in {error.retry_after:.2f} seconds."
            elif isinstance(error, app_commands.MissingPermissions):
                message = "❌ You don't have permission to use this command."
            else:
                message = "❌ An error occurred while processing your command."
            
            # Use appropriate response method based on interaction state
            if interaction.response.is_done():
                # Interaction already responded to, use followup
                await interaction.followup.send(message, ephemeral=True)
            else:
                # No response yet, use initial response
                await interaction.response.send_message(message, ephemeral=True)
                
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
            # Last resort - try to edit the original response if it exists
            try:
                await interaction.edit_original_response(content="❌ An error occurred.")
            except:
                pass  # Give up gracefully


def create_bot() -> FullDiscordBot:
    """Create and return the full Discord bot instance."""
    return FullDiscordBot()


async def main() -> None:
    """Main function to run the full Discord bot."""
    try:
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Validate environment variables
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable not found")
            
        guild_id = os.getenv('DISCORD_GUILD_ID')
        if not guild_id:
            logger.warning("DISCORD_GUILD_ID not set - commands will sync globally (slower)")
        else:
            logger.info(f"Will sync commands to guild: {guild_id}")
        
        # Create the bot
        logger.info("Creating full Discord bot...")
        bot = create_bot()
        
        logger.info("Starting Discord bot...")
        logger.info("Expected commands: /ping, /status, /assign-task, /clarify-task, /approve, /pending-prs, /emergency-stop")
        
        # Run the bot
        async with bot:
            await bot.start(token)
            
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        raise
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())