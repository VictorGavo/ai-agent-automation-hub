# agents/orchestrator/commands.py
"""Discord slash command handlers for the Automation Hub"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import logging

from database.models.task import TaskPriority

logger = logging.getLogger(__name__)

async def setup_commands(bot):
    """Setup all slash commands for the bot"""
    
    @bot.tree.command(name="ping", description="Check if the bot is responsive")
    async def ping_command(interaction: discord.Interaction):
        """Simple ping command to test bot responsiveness"""
        await interaction.response.send_message("🏓 Pong! Automation Hub is online and ready.", ephemeral=True)
    
    @bot.tree.command(name="assign-task", description="Assign a new development task to the AI agents")
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
            # Convert string priority to enum
            task_priority = TaskPriority(priority.lower())
            
            # Process task assignment through orchestrator
            result = await bot.orchestrator.assign_task(
                description=description,
                user_id=str(interaction.user.id),
                channel_id=str(interaction.channel.id),
                priority=task_priority
            )
            
            if result["success"]:
                if result["requires_clarification"]:
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
                    
                    await interaction.followup.send(embed=embed)
                else:
                    # Task assigned successfully
                    embed = discord.Embed(
                        title="✅ Task Assigned Successfully",
                        description=f"**Task:** {description[:200]}...\n\n**Task ID:** `{result['task_id']}`",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Estimated Time:", value=f"{result['estimated_hours']} hours", inline=True)
                    embed.add_field(name="Category:", value=result["category"].title(), inline=True)
                    embed.add_field(name="Priority:", value=priority.title(), inline=True)
                    
                    await interaction.followup.send(embed=embed)
            else:
                # Task assignment failed
                embed = discord.Embed(
                    title="❌ Task Assignment Failed",
                    description=result["message"],
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Task assignment command failed: {e}")
            await interaction.followup.send("⚠️ An error occurred while processing your task. Please try again.")
    
    @bot.tree.command(name="clarify-task", description="Provide clarification for a pending task")
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
            # Collect non-empty answers
            answers = [answer for answer in [answer1, answer2, answer3, answer4, answer5] if answer]
            
            # Process clarification
            result = await bot.orchestrator.provide_clarification(task_id, answers)
            
            if result["success"]:
                embed = discord.Embed(
                    title="✅ Task Clarified and Assigned",
                    description=result["message"],
                    color=discord.Color.green()
                )
                embed.add_field(name="Task ID:", value=f"`{task_id}`", inline=True)
                embed.add_field(name="Estimated Time:", value=f"{result.get('estimated_hours', 'TBD')} hours", inline=True)
                
                await interaction.followup.send(embed=embed)
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
    
    @bot.tree.command(name="status", description="Get current system and task status")
    async def status_command(interaction: discord.Interaction):
        """Display comprehensive system status"""
        await interaction.response.defer()
        
        try:
            status_report = await bot.orchestrator.get_status_report()
            
            embed = discord.Embed(
                title="🤖 Automation Hub Status",
                color=discord.Color.blue()
            )
            
            if "error" in status_report:
                embed.description = f"⚠️ {status_report['error']}"
                embed.color = discord.Color.red()
            else:
                # System status
                embed.add_field(
                    name="🔧 System", 
                    value=f"Status: {status_report['orchestrator_status'].title()}\nUptime: {status_report.get('uptime', 'Unknown')}", 
                    inline=True
                )
                
                # Task statistics
                tasks = status_report.get('tasks', {})
                embed.add_field(
                    name="📋 Tasks",
                    value=f"Total: {tasks.get('total', 0)}\nPending: {tasks.get('pending', 0)}\nCompleted: {tasks.get('completed', 0)}\nSuccess Rate: {tasks.get('success_rate', '0%')}",
                    inline=True
                )
                
                # Agent statistics
                agents = status_report.get('agents', {})
                embed.add_field(
                    name="🤖 Agents",
                    value=f"Active: {agents.get('active', 0)}\nBusy: {agents.get('busy', 0)}\nTotal: {agents.get('total', 0)}",
                    inline=True
                )
                
                # Performance metrics
                performance = status_report.get('performance', {})
                embed.add_field(
                    name="📊 Performance",
                    value=f"Tasks Assigned: {performance.get('tasks_assigned', 0)}\nTasks Completed: {performance.get('tasks_completed', 0)}\nErrors: {performance.get('errors', 0)}\nAvg Response: {performance.get('average_response_time', '0.00s')}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Status command failed: {e}")
            await interaction.followup.send("⚠️ Failed to retrieve system status. Please try again.")
    
    @bot.tree.command(name="logs", description="Get recent system logs")
    @app_commands.describe(
        agent_name="Filter logs by agent name (optional)",
        level="Filter by log level (optional)",
        limit="Number of logs to retrieve (max 20)"
    )
    @app_commands.choices(level=[
        app_commands.Choice(name="All", value="all"),
        app_commands.Choice(name="Error", value="error"),
        app_commands.Choice(name="Warning", value="warning"),
        app_commands.Choice(name="Info", value="info")
    ])
    async def logs_command(
        interaction: discord.Interaction, 
        agent_name: Optional[str] = None,
        level: Optional[str] = "all",
        limit: Optional[int] = 10
    ):
        """Retrieve recent system logs"""
        await interaction.response.defer()
        
        try:
            from database.models.base import SessionLocal
            from database.models.logs import Log, LogLevel
            from sqlalchemy import desc
            
            # Limit the number of logs (max 20 for Discord message limits)
            limit = min(max(1, limit or 10), 20)
            
            db = SessionLocal()
            
            # Build query
            query = db.query(Log).order_by(desc(Log.timestamp))
            
            if agent_name:
                query = query.filter(Log.agent_name == agent_name)
            
            if level and level != "all":
                query = query.filter(Log.level == LogLevel(level.lower()))
            
            logs = query.limit(limit).all()
            
            if logs:
                embed = discord.Embed(
                    title=f"📝 Recent System Logs ({len(logs)} entries)",
                    color=discord.Color.blue()
                )
                
                if agent_name:
                    embed.description = f"Filtered by agent: **{agent_name}**"
                if level and level != "all":
                    embed.description = (embed.description or "") + f"\nFiltered by level: **{level.title()}**"
                
                log_text = ""
                for log in logs:
                    timestamp = log.timestamp.strftime("%m/%d %H:%M:%S")
                    level_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️", "debug": "🔍", "critical": "🚨"}.get(log.level.value, "📝")
                    
                    log_line = f"`{timestamp}` {level_emoji} **{log.agent_name or 'system'}**: {log.message[:100]}\n"
                    
                    if len(log_text + log_line) > 4000:  # Discord embed limit
                        break
                    log_text += log_line
                
                embed.description = (embed.description or "") + f"\n```\n{log_text}\n```"
            else:
                embed = discord.Embed(
                    title="📝 No Logs Found",
                    description="No logs match the specified criteria.",
                    color=discord.Color.orange()
                )
            
            db.close()
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Logs command failed: {e}")
            await interaction.followup.send("⚠️ Failed to retrieve logs. Please try again.")
    
    @bot.tree.command(name="emergency-stop", description="🚨 Emergency stop all agent activities")
    async def emergency_stop_command(interaction: discord.Interaction):
        """Emergency stop command for critical situations"""
        await interaction.response.defer()
        
        try:
            # This is a critical command - require confirmation
            view = EmergencyStopView()
            
            embed = discord.Embed(
                title="🚨 Emergency Stop Requested",
                description="This will immediately halt all agent activities.\nAre you sure you want to proceed?",
                color=discord.Color.red()
            )
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Emergency stop command failed: {e}")
            await interaction.followup.send("⚠️ Emergency stop command failed. Please contact system administrator.")

class EmergencyStopView(discord.ui.View):
    """Confirmation view for emergency stop"""
    
    def __init__(self):
        super().__init__(timeout=30.0)
    
    @discord.ui.button(label="Confirm Emergency Stop", style=discord.ButtonStyle.danger, emoji="🚨")
    async def confirm_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm emergency stop"""
        try:
            # TODO: Implement actual emergency stop logic
            # For now, just update orchestrator status
            bot = interaction.client
            await bot.orchestrator.update_status(bot.orchestrator.status.__class__.OFFLINE)
            
            embed = discord.Embed(
                title="🚨 Emergency Stop Activated",
                description="All agent activities have been halted.\nUse `/status` to check system state.",
                color=discord.Color.red()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            logger.error(f"Emergency stop confirmation failed: {e}")
            await interaction.response.send_message("⚠️ Emergency stop failed. Please restart services manually.", ephemeral=True)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel emergency stop"""
        embed = discord.Embed(
            title="Emergency Stop Cancelled",
            description="Agent activities continue normally.",
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def on_timeout(self):
        """Handle timeout"""
        for item in self.children:
            item.disabled = True