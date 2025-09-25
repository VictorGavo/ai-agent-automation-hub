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
        
        # Setup slash commands from orchestrator commands
        self._setup_commands()
        
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
            await interaction.response.send_message("🏓 Pong! Automation Hub is online and ready.", ephemeral=True)
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
            await interaction.response.defer()
            
            try:
                if self.orchestrator and hasattr(self.orchestrator, 'assign_task'):
                    # Use full orchestrator if available
                    if TaskPriority:
                        task_priority = TaskPriority(priority.lower())
                    else:
                        task_priority = priority.lower()
                    
                    result = await self.orchestrator.assign_task(
                        description=description,
                        user_id=str(interaction.user.id),
                        channel_id=str(interaction.channel.id),
                        priority=task_priority
                    )
                    
                    if result["success"]:
                        if result.get("requires_clarification"):
                            # Create clarification embed
                            embed = discord.Embed(
                                title="🤔 Task Needs Clarification",
                                description=f"**Task:** {description[:200]}...\n\n**Task ID:** `{result['task_id']}`",
                                color=discord.Color.orange()
                            )
                            
                            # Add clarifying questions
                            questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(result["questions"])])
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
                    else:
                        # Task assignment failed
                        embed = discord.Embed(
                            title="❌ Task Assignment Failed",
                            description=result["message"],
                            color=discord.Color.red()
                        )
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
                    
                    embed = discord.Embed(
                        title="✅ Task Assigned (Simplified)",
                        description=f"**Task ID:** `{task_id}`\n**Priority:** {priority.title()}",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Description", value=description[:500], inline=False)
                    embed.add_field(name="Note", value="Full orchestrator not available - basic assignment used", inline=False)
                
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
            await interaction.response.defer()
            
            try:
                if self.orchestrator and hasattr(self.orchestrator, 'provide_clarification'):
                    # Collect non-empty answers
                    answers = [answer for answer in [answer1, answer2, answer3, answer4, answer5] if answer]
                    
                    # Process clarification
                    result = await self.orchestrator.provide_clarification(task_id, answers)
                    
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
                else:
                    embed = discord.Embed(
                        title="❌ Orchestrator Not Available",
                        description="Task clarification requires full orchestrator integration",
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
            await interaction.response.defer()
            
            try:
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
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Status command failed: {e}")
                await interaction.followup.send("⚠️ Failed to retrieve system status. Please try again.")
        
        # ============ PR MANAGEMENT COMMANDS ============
        
        @self.tree.command(name="approve", description="Approve and merge a specific pull request")
        @app_commands.describe(pr_number="The pull request number to approve and merge")
        async def approve_pr_command(interaction: discord.Interaction, pr_number: int):
            """Approve and merge a pull request"""
            await interaction.response.defer()
            
            try:
                if self.orchestrator and hasattr(self.orchestrator, 'approve_and_merge_pr'):
                    result = await self.orchestrator.approve_and_merge_pr(pr_number, str(interaction.user.id))
                    
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
                else:
                    embed = discord.Embed(
                        title="❌ GitHub Integration Not Available",
                        description="PR approval requires full orchestrator with GitHub integration",
                        color=discord.Color.red()
                    )
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Approve PR command failed: {e}")
                await interaction.followup.send("⚠️ An error occurred while approving the PR. Please try again.")
        
        @self.tree.command(name="pending-prs", description="Show all open pull requests awaiting approval")
        @app_commands.describe(limit="Maximum number of PRs to show (default: 10)")
        async def pending_prs_command(interaction: discord.Interaction, limit: Optional[int] = 10):
            """Display all pending pull requests"""
            await interaction.response.defer()
            
            try:
                # Limit the number to reasonable bounds
                limit = min(max(1, limit or 10), 20)
                
                if self.orchestrator and hasattr(self.orchestrator, 'list_pending_prs'):
                    result = await self.orchestrator.list_pending_prs(limit)
                    
                    if not result["success"]:
                        embed = discord.Embed(
                            title="❌ Failed to Load PRs",
                            description=result["message"],
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                        return
                    
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
                else:
                    embed = discord.Embed(
                        title="❌ GitHub Integration Not Available",
                        description="PR listing requires full orchestrator with GitHub integration",
                        color=discord.Color.red()
                    )
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Pending PRs command failed: {e}")
                await interaction.followup.send("⚠️ An error occurred while retrieving pending PRs. Please try again.")
        
        @self.tree.command(name="emergency-stop", description="🚨 Emergency stop all agent activities")
        async def emergency_stop_command(interaction: discord.Interaction):
            """Emergency stop command for critical situations"""
            await interaction.response.defer()
            
            try:
                if self.orchestrator and hasattr(self.orchestrator, 'update_status'):
                    # TODO: Implement proper emergency stop
                    embed = discord.Embed(
                        title="🚨 Emergency Stop Activated",
                        description="All agent activities have been halted.\nUse `/status` to check system state.",
                        color=discord.Color.red()
                    )
                    self.agent_status = {k: 'stopped' for k in self.agent_status.keys()}
                else:
                    embed = discord.Embed(
                        title="🚨 Emergency Stop (Basic)",
                        description="Bot commands disabled. Restart required for full functionality.",
                        color=discord.Color.red()
                    )
                    self.agent_status = {k: 'stopped' for k in self.agent_status.keys()}
                
                await interaction.followup.send(embed=embed)
                
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
        
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏰ Command on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ An error occurred while processing your command.",
                ephemeral=True
            )


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