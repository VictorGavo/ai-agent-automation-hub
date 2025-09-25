"""
Discord Safety Commands

Discord slash commands for the reliability system including:
- /rollback - List and select rollback points
- /safe-mode - Pause all agents, enable manual control only
- /resume-task - Resume interrupted agent work
- /system-health - Show reliability status and any issues
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import discord
from discord import app_commands

from safety_monitor import get_safety_monitor
from utils.task_state_manager import get_task_state_manager, TaskState
from utils.safe_git_operations import get_safe_git_operations

logger = logging.getLogger(__name__)


class SafetyCommandsMixin:
    """
    Mixin class to add safety commands to the Discord bot.
    
    This should be mixed into the main bot class to provide reliability features.
    """
    
    def setup_safety_commands(self) -> None:
        """Set up all safety-related slash commands."""
        
        @self.tree.command(name="system-health", description="🏥 Show system health and reliability status")
        async def system_health_command(interaction: discord.Interaction):
            """Display comprehensive system health status."""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                timeout_seconds = 20
                
                async def get_health_with_timeout():
                    safety_monitor = get_safety_monitor()
                    health = safety_monitor.get_system_health()
                    return health
                
                # Execute with timeout
                try:
                    health = await asyncio.wait_for(get_health_with_timeout(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    await interaction.followup.send("⏱️ System health check is taking longer than expected. Please try again in a moment.")
                    logger.warning(f"System health timeout for user {interaction.user}")
                    return
                
                # Create main embed
                if health.get('is_overloaded', False):
                    embed_color = discord.Color.red()
                    status_icon = "🚨"
                    status_text = "System Overloaded"
                elif health.get('warnings', []):
                    embed_color = discord.Color.orange()
                    status_icon = "⚠️"
                    status_text = "Warnings Present"
                else:
                    embed_color = discord.Color.green()
                    status_icon = "✅"
                    status_text = "System Healthy"
                
                embed = discord.Embed(
                    title=f"{status_icon} System Health Report",
                    description=f"**Status:** {status_text}\n**Timestamp:** <t:{int(datetime.now().timestamp())}:R>",
                    color=embed_color
                )
                
                # System metrics
                metrics = health.get('system_metrics', {})
                cpu = metrics.get('cpu_percent', 0)
                memory = metrics.get('memory_percent', 0)
                disk = metrics.get('disk_percent', 0)
                temp = metrics.get('temperature')
                
                system_value = f"🔧 CPU: {cpu:.1f}%\n💾 Memory: {memory:.1f}%\n💿 Disk: {disk:.1f}%"
                if temp:
                    system_value += f"\n🌡️ Temperature: {temp:.1f}°C"
                
                embed.add_field(
                    name="System Resources",
                    value=system_value,
                    inline=True
                )
                
                # Agent status
                safe_mode = health.get('safe_mode_active', False)
                paused_agents = health.get('paused_agents', [])
                monitoring = health.get('monitoring_active', False)
                
                agent_value = f"🤖 Safe Mode: {'🔴 Active' if safe_mode else '🟢 Inactive'}\n"
                agent_value += f"⏸️ Paused Agents: {len(paused_agents)}\n"
                agent_value += f"👁️ Monitoring: {'🟢 Active' if monitoring else '🔴 Inactive'}"
                
                embed.add_field(
                    name="Agent Control",
                    value=agent_value,
                    inline=True
                )
                
                # Git status
                git_status = health.get('git_status', {})
                current_branch = git_status.get('current_branch', 'unknown')
                is_safe_branch = git_status.get('is_safe_branch', False)
                backup_count = git_status.get('backup_branches_available', 0)
                
                git_value = f"🌿 Branch: {current_branch}\n"
                git_value += f"🛡️ Safe: {'✅' if is_safe_branch else '❌'}\n"
                git_value += f"💾 Backups: {backup_count}"
                
                embed.add_field(
                    name="Git Safety",
                    value=git_value,
                    inline=True
                )
                
                # Recent alerts
                recent_alerts = health.get('recent_alerts', [])
                if recent_alerts:
                    alert_text = ""
                    for alert in recent_alerts[:3]:  # Show top 3
                        level_icon = {
                            'critical': '🚨',
                            'error': '❌',
                            'warning': '⚠️',
                            'info': 'ℹ️'
                        }.get(alert.get('level'), 'ℹ️')
                        
                        alert_time = datetime.fromisoformat(alert['timestamp'])
                        alert_text += f"{level_icon} {alert['title']}\n"
                    
                    embed.add_field(
                        name="Recent Alerts",
                        value=alert_text or "None",
                        inline=False
                    )
                
                # Warnings
                warnings = health.get('warnings', [])
                if warnings:
                    warning_text = "\n".join([f"• {w}" for w in warnings[:5]])
                    embed.add_field(
                        name="⚠️ System Warnings",
                        value=warning_text,
                        inline=False
                    )
                
                # Add action buttons if needed
                if safe_mode or health.get('is_overloaded'):
                    embed.set_footer(text="💡 Use /safe-mode to control agent operations")
                elif warnings:
                    embed.set_footer(text="💡 Use /rollback for recovery options")
                else:
                    embed.set_footer(text="💡 System operating normally")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"System health command failed: {e}")
                await interaction.followup.send("❌ Failed to retrieve system health status.")
        
        @self.tree.command(name="safe-mode", description="🔒 Control safe mode (pause/resume all agents)")
        @app_commands.describe(
            action="Enable or disable safe mode",
            reason="Reason for safe mode activation (required when enabling)"
        )
        @app_commands.choices(action=[
            app_commands.Choice(name="Enable (Pause All Agents)", value="enable"),
            app_commands.Choice(name="Disable (Resume Operations)", value="disable"),
            app_commands.Choice(name="Status", value="status")
        ])
        async def safe_mode_command(
            interaction: discord.Interaction, 
            action: str,
            reason: Optional[str] = None
        ):
            """Control system safe mode."""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                timeout_seconds = 15
                
                async def handle_safe_mode_with_timeout():
                    safety_monitor = get_safety_monitor()
                    return safety_monitor
                
                # Execute with timeout
                try:
                    safety_monitor = await asyncio.wait_for(handle_safe_mode_with_timeout(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    await interaction.followup.send("⏱️ Safe mode operation is taking longer than expected. Please try again.")
                    logger.warning(f"Safe mode timeout for user {interaction.user}")
                    return
                
                if action == "enable":
                    if not reason:
                        await interaction.followup.send(
                            "❌ Reason is required when enabling safe mode.",
                            ephemeral=True
                        )
                        return
                    
                    safety_monitor.activate_safe_mode(f"Discord command by {interaction.user}: {reason}")
                    
                    embed = discord.Embed(
                        title="🔒 Safe Mode Activated",
                        description=f"All agent operations have been paused.\n\n**Reason:** {reason}",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Next Steps",
                        value="• Use `/safe-mode disable` to resume operations\n• Use `/system-health` to monitor status\n• Use `/rollback` for recovery options",
                        inline=False
                    )
                    embed.set_footer(text=f"Activated by {interaction.user.display_name}")
                
                elif action == "disable":
                    safety_monitor.deactivate_safe_mode()
                    
                    embed = discord.Embed(
                        title="🟢 Safe Mode Deactivated",
                        description="Agent operations have been resumed.",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="Status",
                        value="• All agents can now operate normally\n• Monitoring continues in background\n• Use `/system-health` to verify status",
                        inline=False
                    )
                    embed.set_footer(text=f"Deactivated by {interaction.user.display_name}")
                
                else:  # status
                    is_active = safety_monitor.safe_mode_active
                    paused_agents = safety_monitor.paused_agents
                    
                    embed = discord.Embed(
                        title="🔍 Safe Mode Status",
                        color=discord.Color.red() if is_active else discord.Color.green()
                    )
                    
                    status_text = "🔴 Active" if is_active else "🟢 Inactive"
                    embed.add_field(name="Safe Mode", value=status_text, inline=True)
                    embed.add_field(name="Paused Agents", value=str(len(paused_agents)), inline=True)
                    
                    if paused_agents:
                        agent_list = "\n".join([f"• {agent}" for agent in paused_agents])
                        embed.add_field(name="Currently Paused", value=agent_list, inline=False)
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Safe mode command failed: {e}")
                await interaction.followup.send("❌ Failed to control safe mode.")
        
        @self.tree.command(name="rollback", description="🔄 View and select rollback options")
        @app_commands.describe(
            agent_name="Specific agent to show rollback options for (optional)",
            rollback_type="Type of rollback to perform"
        )
        @app_commands.choices(rollback_type=[
            app_commands.Choice(name="Show Options Only", value="show"),
            app_commands.Choice(name="Git Rollback to Last Backup", value="git_backup"),
            app_commands.Choice(name="Task Checkpoint Rollback", value="task_checkpoint")
        ])
        async def rollback_command(
            interaction: discord.Interaction,
            rollback_type: str = "show",
            agent_name: Optional[str] = None
        ):
            """Display rollback options and perform rollbacks."""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                timeout_seconds = 25
                
                # Add a simple timeout check but continue with normal processing
                # This is mainly to prevent the defer() from timing out
                if rollback_type == "show":
                    # Show available rollback options
                    task_manager = get_task_state_manager()
                    safe_git = get_safe_git_operations()
                    
                    embed = discord.Embed(
                        title="🔄 Available Rollback Options",
                        description="Recovery options for system restoration",
                        color=discord.Color.blue()
                    )
                    
                    # Git rollback options
                    git_options = safe_git.get_rollback_options()
                    backup_branches = git_options.get('backup_branches', [])
                    recent_commits = git_options.get('recent_commits', [])
                    
                    git_text = f"**Current Branch:** {git_options.get('current_branch', 'unknown')}\n"
                    git_text += f"**Backup Branches:** {len(backup_branches)}\n"
                    git_text += f"**Recent Commits:** {len(recent_commits)}"
                    
                    embed.add_field(
                        name="🌿 Git Recovery",
                        value=git_text,
                        inline=True
                    )
                    
                    # Task checkpoint options
                    if agent_name:
                        recovery_options = task_manager.get_recovery_options(agent_name)
                        interrupted_tasks = recovery_options.get('interrupted_tasks', [])
                        checkpoints = recovery_options.get('recent_checkpoints', [])
                        
                        task_text = f"**Agent:** {agent_name}\n"
                        task_text += f"**Interrupted Tasks:** {len(interrupted_tasks)}\n"
                        task_text += f"**Available Checkpoints:** {len(checkpoints)}"
                    else:
                        # Show summary for all agents
                        task_text = "**All Agents**\n"
                        task_text += "Specify agent_name for detailed options"
                    
                    embed.add_field(
                        name="📋 Task Recovery",
                        value=task_text,
                        inline=True
                    )
                    
                    # Show specific backup branches if available
                    if backup_branches:
                        branch_list = "\n".join([f"• `{branch}`" for branch in backup_branches[:5]])
                        if len(backup_branches) > 5:
                            branch_list += f"\n• ... and {len(backup_branches) - 5} more"
                        
                        embed.add_field(
                            name="💾 Backup Branches",
                            value=branch_list,
                            inline=False
                        )
                    
                    embed.add_field(
                        name="🚀 Quick Actions",
                        value="• `/rollback git_backup` - Rollback to latest backup branch\n• `/rollback task_checkpoint [agent]` - Rollback agent to checkpoint\n• `/safe-mode enable` - Pause all operations first",
                        inline=False
                    )
                
                elif rollback_type == "git_backup":
                    # Perform git rollback to latest backup
                    safe_git = get_safe_git_operations()
                    git_options = safe_git.get_rollback_options()
                    backup_branches = git_options.get('backup_branches', [])
                    
                    if not backup_branches:
                        embed = discord.Embed(
                            title="❌ No Backup Branches Available",
                            description="No backup branches found for rollback.",
                            color=discord.Color.red()
                        )
                    else:
                        # Use the most recent backup branch
                        latest_backup = backup_branches[0]  # Assuming sorted by date
                        
                        operation = safe_git.rollback_to_backup(
                            latest_backup, 
                            f"Discord-{interaction.user.name}"
                        )
                        
                        if operation.status.value == "completed":
                            embed = discord.Embed(
                                title="✅ Git Rollback Successful",
                                description=f"Successfully rolled back to backup branch: `{latest_backup}`",
                                color=discord.Color.green()
                            )
                            embed.add_field(
                                name="Operation Details",
                                value=f"**Operation ID:** `{operation.operation_id}`\n**Branch:** `{latest_backup}`\n**Timestamp:** <t:{int(operation.timestamp.timestamp())}:R>",
                                inline=False
                            )
                        else:
                            embed = discord.Embed(
                                title="❌ Git Rollback Failed",
                                description=f"Rollback operation failed: {operation.error_message}",
                                color=discord.Color.red()
                            )
                
                elif rollback_type == "task_checkpoint":
                    if not agent_name:
                        embed = discord.Embed(
                            title="❌ Agent Name Required",
                            description="Please specify an agent name for checkpoint rollback.",
                            color=discord.Color.red()
                        )
                    else:
                        # Show available checkpoints for the agent
                        task_manager = get_task_state_manager()
                        recovery_options = task_manager.get_recovery_options(agent_name)
                        checkpoints = recovery_options.get('recent_checkpoints', [])
                        
                        if not checkpoints:
                            embed = discord.Embed(
                                title=f"❌ No Checkpoints for {agent_name}",
                                description="No available checkpoints for rollback.",
                                color=discord.Color.red()
                            )
                        else:
                            embed = discord.Embed(
                                title=f"🔄 Available Checkpoints for {agent_name}",
                                description="Select a checkpoint to rollback to using `/resume-task`",
                                color=discord.Color.blue()
                            )
                            
                            for i, checkpoint in enumerate(checkpoints[:5]):
                                checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
                                embed.add_field(
                                    name=f"Checkpoint {i+1}",
                                    value=f"**ID:** `{checkpoint['checkpoint_id'][:8]}...`\n**Type:** {checkpoint['type']}\n**Step:** {checkpoint['step']}\n**Time:** <t:{int(checkpoint_time.timestamp())}:R>",
                                    inline=True
                                )
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Rollback command failed: {e}")
                await interaction.followup.send("❌ Failed to process rollback request.")
        
        @self.tree.command(name="resume-task", description="▶️ Resume interrupted agent task from checkpoint")
        @app_commands.describe(
            task_id="Task ID to resume",
            checkpoint_id="Specific checkpoint ID to resume from (optional)"
        )
        async def resume_task_command(
            interaction: discord.Interaction,
            task_id: str,
            checkpoint_id: Optional[str] = None
        ):
            """Resume an interrupted task."""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                task_manager = get_task_state_manager()
                
                # Get task state
                task_state = task_manager.get_task_state(task_id)
                if not task_state:
                    embed = discord.Embed(
                        title="❌ Task Not Found",
                        description=f"Task `{task_id}` not found in the system.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Check if task can be resumed
                if task_state.state not in [TaskState.PAUSED, TaskState.IN_PROGRESS, TaskState.FAILED]:
                    embed = discord.Embed(
                        title="❌ Cannot Resume Task",
                        description=f"Task is in `{task_state.state.value}` state and cannot be resumed.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Get available checkpoints
                checkpoints = task_manager.get_task_checkpoints(task_id)
                
                if not checkpoints:
                    embed = discord.Embed(
                        title="❌ No Checkpoints Available",
                        description="No checkpoints found for this task.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Select checkpoint
                if checkpoint_id:
                    selected_checkpoint = None
                    for cp in checkpoints:
                        if cp.checkpoint_id.startswith(checkpoint_id):
                            selected_checkpoint = cp
                            break
                    
                    if not selected_checkpoint:
                        embed = discord.Embed(
                            title="❌ Checkpoint Not Found",
                            description=f"Checkpoint `{checkpoint_id}` not found.",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=embed)
                        return
                else:
                    # Use the most recent checkpoint
                    selected_checkpoint = checkpoints[0]
                
                # Attempt to resume (this would need agent integration)
                embed = discord.Embed(
                    title="🔄 Task Resume Initiated",
                    description=f"Attempting to resume task from checkpoint...",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="Task Details",
                    value=f"**Task ID:** `{task_id}`\n**Agent:** {task_state.agent_name}\n**Description:** {task_state.task_description[:100]}...",
                    inline=False
                )
                
                embed.add_field(
                    name="Checkpoint Details",
                    value=f"**ID:** `{selected_checkpoint.checkpoint_id[:8]}...`\n**Type:** {selected_checkpoint.checkpoint_type.value}\n**Step:** {selected_checkpoint.current_step}\n**Progress:** {selected_checkpoint.progress_percentage:.1f}%",
                    inline=False
                )
                
                embed.set_footer(text="Note: Actual resume requires agent integration")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Resume task command failed: {e}")
                await interaction.followup.send("❌ Failed to resume task.")
        
        @self.tree.command(name="pause-agent", description="⏸️ Pause specific agent operations")
        @app_commands.describe(
            agent_name="Name of the agent to pause",
            reason="Reason for pausing the agent"
        )
        async def pause_agent_command(
            interaction: discord.Interaction,
            agent_name: str,
            reason: str
        ):
            """Pause a specific agent."""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                safety_monitor = get_safety_monitor()
                safety_monitor.pause_agent(agent_name, f"Discord command by {interaction.user}: {reason}")
                
                embed = discord.Embed(
                    title=f"⏸️ Agent Paused: {agent_name}",
                    description=f"Agent `{agent_name}` has been paused.",
                    color=discord.Color.orange()
                )
                
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(
                    name="Next Steps",
                    value=f"• Use `/resume-agent {agent_name}` to resume\n• Use `/system-health` to monitor status",
                    inline=False
                )
                embed.set_footer(text=f"Paused by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Pause agent command failed: {e}")
                await interaction.followup.send("❌ Failed to pause agent.")
        
        @self.tree.command(name="resume-agent", description="▶️ Resume paused agent operations")
        @app_commands.describe(agent_name="Name of the agent to resume")
        async def resume_agent_command(interaction: discord.Interaction, agent_name: str):
            """Resume a paused agent."""
            # CRITICAL: Defer immediately to prevent timeout
            await interaction.response.defer()
            
            try:
                safety_monitor = get_safety_monitor()
                
                if not safety_monitor.is_agent_paused(agent_name):
                    embed = discord.Embed(
                        title=f"ℹ️ Agent Not Paused: {agent_name}",
                        description=f"Agent `{agent_name}` is not currently paused.",
                        color=discord.Color.blue()
                    )
                else:
                    safety_monitor.resume_agent(agent_name)
                    
                    embed = discord.Embed(
                        title=f"▶️ Agent Resumed: {agent_name}",
                        description=f"Agent `{agent_name}` has been resumed and can operate normally.",
                        color=discord.Color.green()
                    )
                    embed.set_footer(text=f"Resumed by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Resume agent command failed: {e}")
                await interaction.followup.send("❌ Failed to resume agent.")
        
        logger.info("Safety commands setup complete: /system-health, /safe-mode, /rollback, /resume-task, /pause-agent, /resume-agent")


def setup_safety_commands(bot_instance) -> None:
    """
    Standalone function to setup safety commands on a bot instance.
    
    Args:
        bot_instance: Discord bot instance with tree attribute
    """
    mixin = SafetyCommandsMixin()
    mixin.tree = bot_instance.tree  # Assign the command tree
    mixin.setup_safety_commands()
    logger.info("Safety commands added to bot instance")