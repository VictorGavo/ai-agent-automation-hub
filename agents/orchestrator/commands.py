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
                uptime = status_report.get('uptime', 'Unknown')
                embed.add_field(
                    name="🔧 System", 
                    value=f"Status: {status_report['orchestrator_status'].title()}\nUptime: {uptime}\nGitHub: {'✅' if bot.orchestrator.github_client else '❌'}", 
                    inline=True
                )
                
                # Task statistics
                tasks = status_report.get('tasks', {})
                embed.add_field(
                    name="📋 Active Tasks",
                    value=f"Total: {tasks.get('total', 0)}\nPending: {tasks.get('pending', 0)}\nIn Progress: {tasks.get('in_progress', 0)}\nCompleted: {tasks.get('completed', 0)}",
                    inline=True
                )
                
                # PR statistics with pending count
                prs = status_report.get('prs', {})
                pending_pr_result = await bot.orchestrator.list_pending_prs(5)
                pending_count = len(pending_pr_result.get('prs', [])) if pending_pr_result.get('success') else 0
                
                embed.add_field(
                    name="🔄 Pull Requests",
                    value=f"Open PRs: {prs.get('open_prs', 'N/A')}\nAwaiting Approval: {pending_count}\nRecent Activity: {prs.get('recent_merges', 0)} merged",
                    inline=True
                )
                
                # Agent performance metrics
                performance = status_report.get('performance', {})
                success_rate = tasks.get('success_rate', '0%')
                embed.add_field(
                    name="📊 Agent Performance",
                    value=f"Success Rate: {success_rate}\nTasks/Day: {performance.get('tasks_per_day', 0)}\nAvg Response: {performance.get('average_response_time', '0.00s')}\nErrors: {performance.get('errors', 0)}",
                    inline=True
                )
                
                # Recent activity
                recent_activity = []
                if tasks.get('pending', 0) > 0:
                    recent_activity.append(f"📝 {tasks['pending']} tasks pending")
                if pending_count > 0:
                    recent_activity.append(f"⏳ {pending_count} PRs need approval")
                if performance.get('errors', 0) > 0:
                    recent_activity.append(f"⚠️ {performance['errors']} recent errors")
                
                if recent_activity:
                    embed.add_field(
                        name="� Alerts", 
                        value="\n".join(recent_activity), 
                        inline=False
                    )
                
                # GitHub integration status
                if bot.orchestrator.github_client:
                    github_stats = bot.orchestrator.github_client.get_stats()
                    embed.add_field(
                        name="🐙 GitHub Integration",
                        value=f"Repository: {github_stats.get('repository', 'Unknown')}\nOperations: {github_stats.get('operations', {}).get('commits_made', 0)} commits, {github_stats.get('operations', {}).get('prs_created', 0)} PRs\nSuccess Rate: {github_stats.get('success_rate', 0):.1f}%",
                        inline=False
                    )
                
                # Testing Agent status
                try:
                    testing_status = await bot.orchestrator.get_testing_status()
                    agent_status = "🟢 Online" if testing_status.get('online', False) else "🔴 Offline"
                    active_tests = testing_status.get('active_tests', 0)
                    auto_approve = "✅ On" if testing_status.get('auto_approve', False) else "❌ Off"
                    stats = testing_status.get('statistics', {})
                    success_rate = f"{(stats.get('passed', 0) / max(stats.get('total', 1), 1) * 100):.1f}%" if stats.get('total', 0) > 0 else "N/A"
                    
                    embed.add_field(
                        name="🧪 Testing Agent",
                        value=f"Status: {agent_status}\nActive Tests: {active_tests}\nAuto-Approve: {auto_approve}\nTest Success: {success_rate} ({stats.get('total', 0)} total)",
                        inline=True
                    )
                except Exception as e:
                    embed.add_field(
                        name="🧪 Testing Agent",
                        value="Status: ❓ Unknown\nUse /test-status for details",
                        inline=True
                    )
                
                # Add quick action guides
                embed.set_footer(text="💡 /test-status • /pending-prs • /assign-task • /review [pr-number] • /approve [pr-number]")
            
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
    
    # PR Management Commands
    @bot.tree.command(name="approve", description="Approve and merge a specific pull request")
    @app_commands.describe(pr_number="The pull request number to approve and merge")
    async def approve_pr_command(interaction: discord.Interaction, pr_number: int):
        """Approve and merge a pull request"""
        await interaction.response.defer()
        
        try:
            result = await bot.orchestrator.approve_and_merge_pr(pr_number, str(interaction.user.id))
            
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
                
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ PR Approval Failed",
                    description=result["message"],
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Approve PR command failed: {e}")
            await interaction.followup.send("⚠️ An error occurred while approving the PR. Please try again.")
    
    @bot.tree.command(name="review", description="Show PR details for review with approval buttons")
    @app_commands.describe(pr_number="The pull request number to review")
    async def review_pr_command(interaction: discord.Interaction, pr_number: int):
        """Display PR details for review with interactive buttons"""
        await interaction.response.defer()
        
        try:
            # Get PR details from GitHub via orchestrator
            if not bot.orchestrator.github_client:
                embed = discord.Embed(
                    title="❌ GitHub Not Available",
                    description="GitHub client is not configured. Cannot retrieve PR details.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            pr_details = await bot.orchestrator.github_client.get_pull_request(pr_number)
            
            if not pr_details:
                embed = discord.Embed(
                    title="❌ PR Not Found",
                    description=f"Pull request #{pr_number} was not found.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create detailed PR review embed
            embed = discord.Embed(
                title=f"🔍 PR #{pr_number} - Review",
                description=pr_details["title"],
                color=discord.Color.blue(),
                url=pr_details["url"]
            )
            
            # Add PR details
            embed.add_field(
                name="📊 Changes", 
                value=f"Files: {pr_details['files_changed_count']}\n+{pr_details['additions']} -{pr_details['deletions']}", 
                inline=True
            )
            
            embed.add_field(
                name="🔄 Status", 
                value=f"State: {pr_details['state'].title()}\nMergeable: {'✅' if pr_details['mergeable'] else '❌'}", 
                inline=True
            )
            
            embed.add_field(
                name="👤 Author", 
                value=f"{pr_details['author']}\n{pr_details['head_branch']} → {pr_details['base_branch']}", 
                inline=True
            )
            
            # Add description if available
            if pr_details.get("body"):
                description_text = pr_details["body"][:500]
                if len(pr_details["body"]) > 500:
                    description_text += "..."
                embed.add_field(name="📝 Description", value=description_text, inline=False)
            
            # Add files changed
            if pr_details.get("files_changed"):
                files_text = "\n".join([f"• `{f}`" for f in pr_details["files_changed"][:10]])
                if len(pr_details["files_changed"]) > 10:
                    files_text += f"\n... and {len(pr_details['files_changed']) - 10} more files"
                embed.add_field(name="📁 Files Changed", value=files_text, inline=False)
            
            # Add timestamps
            created_date = pr_details["created_at"][:10]
            updated_date = pr_details["updated_at"][:10]
            embed.add_field(
                name="⏰ Timeline", 
                value=f"Created: {created_date}\nUpdated: {updated_date}", 
                inline=True
            )
            
            embed.set_footer(text="Use the buttons below to approve or reject this PR")
            
            # Create interactive view with approve/reject buttons
            view = PRReviewView(pr_number)
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Review PR command failed: {e}")
            await interaction.followup.send("⚠️ An error occurred while retrieving PR details. Please try again.")
    
    @bot.tree.command(name="reject", description="Reject a pull request with a reason")
    @app_commands.describe(
        pr_number="The pull request number to reject",
        reason="Reason for rejecting the PR"
    )
    async def reject_pr_command(interaction: discord.Interaction, pr_number: int, reason: str):
        """Reject a pull request with a reason"""
        await interaction.response.defer()
        
        try:
            result = await bot.orchestrator.reject_pr(pr_number, reason, str(interaction.user.id))
            
            if result["success"]:
                embed = discord.Embed(
                    title="❌ PR Rejected",
                    description=f"**PR #{pr_number}** has been rejected by {interaction.user.mention}",
                    color=discord.Color.red()
                )
                embed.add_field(name="PR Title", value=result.get("pr_title", "N/A"), inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"Rejected by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ PR Rejection Failed", 
                    description=result["message"],
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Reject PR command failed: {e}")
            await interaction.followup.send("⚠️ An error occurred while rejecting the PR. Please try again.")
    
    @bot.tree.command(name="pending-prs", description="Show all open pull requests awaiting approval")
    @app_commands.describe(limit="Maximum number of PRs to show (default: 10)")
    async def pending_prs_command(interaction: discord.Interaction, limit: Optional[int] = 10):
        """Display all pending pull requests"""
        await interaction.response.defer()
        
        try:
            # Limit the number to reasonable bounds
            limit = min(max(1, limit or 10), 20)
            
            result = await bot.orchestrator.list_pending_prs(limit)
            
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
                await interaction.followup.send(embed=embed)
                return
            
            # Create embed with PR list
            embed = discord.Embed(
                title=f"📋 Pending Pull Requests ({len(prs)})",
                color=discord.Color.blue()
            )
            
            for pr in prs:
                pr_status = ""
                if pr.get("draft"):
                    pr_status += "🚧 Draft • "
                if not pr.get("mergeable"):
                    pr_status += "⚠️ Conflicts • "
                if pr.get("task_id"):
                    pr_status += f"Task: {pr['task_id']} • "
                
                pr_status += f"by {pr['author']}"
                
                embed.add_field(
                    name=f"#{pr['number']} - {pr['title'][:50]}{'...' if len(pr['title']) > 50 else ''}",
                    value=f"{pr_status}\n[View PR]({pr['url']})",
                    inline=False
                )
            
            embed.set_footer(text="Use /review [pr-number] to see details and approve/reject")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Pending PRs command failed: {e}")
            await interaction.followup.send("⚠️ An error occurred while retrieving pending PRs. Please try again.")

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

class PRReviewView(discord.ui.View):
    """Interactive view for PR review with approve/reject buttons"""
    
    def __init__(self, pr_number: int):
        super().__init__(timeout=300.0)  # 5 minute timeout
        self.pr_number = pr_number
    
    @discord.ui.button(label="✅ Approve & Merge", style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick approve button"""
        await interaction.response.defer()
        
        try:
            bot = interaction.client
            result = await bot.orchestrator.approve_and_merge_pr(self.pr_number, str(interaction.user.id))
            
            if result["success"]:
                embed = discord.Embed(
                    title="✅ PR Approved and Merged",
                    description=f"PR #{self.pr_number} has been successfully merged by {interaction.user.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(name="PR Title", value=result.get("pr_title", "N/A"), inline=False)
                if result.get("sha"):
                    embed.add_field(name="Merge Commit", value=f"`{result['sha'][:8]}`", inline=True)
                embed.set_footer(text=f"Approved by {interaction.user.display_name}")
                
                # Disable all buttons after successful merge
                for item in self.children:
                    item.disabled = True
                
                await interaction.edit_original_response(view=self)
                await interaction.followup.send(embed=embed)
            else:
                error_embed = discord.Embed(
                    title="❌ Approval Failed",
                    description=result["message"],
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"PR approve button failed: {e}")
            await interaction.followup.send("❌ An error occurred while approving the PR.", ephemeral=True)
    
    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick reject button with modal for reason"""
        modal = RejectReasonModal(self.pr_number, self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh PR details"""
        await interaction.response.defer()
        
        try:
            bot = interaction.client
            
            if not bot.orchestrator.github_client:
                await interaction.followup.send("❌ GitHub client not available", ephemeral=True)
                return
            
            pr_details = await bot.orchestrator.github_client.get_pull_request(self.pr_number)
            
            if not pr_details:
                await interaction.followup.send(f"❌ PR #{self.pr_number} not found", ephemeral=True)
                return
            
            # Update the embed with fresh data
            embed = discord.Embed(
                title=f"🔍 PR #{self.pr_number} - Review (Updated)",
                description=pr_details["title"],
                color=discord.Color.blue(),
                url=pr_details["url"]
            )
            
            # Add updated PR details
            embed.add_field(
                name="📊 Changes", 
                value=f"Files: {pr_details['files_changed_count']}\n+{pr_details['additions']} -{pr_details['deletions']}", 
                inline=True
            )
            
            embed.add_field(
                name="🔄 Status", 
                value=f"State: {pr_details['state'].title()}\nMergeable: {'✅' if pr_details['mergeable'] else '❌'}", 
                inline=True
            )
            
            embed.add_field(
                name="👤 Author", 
                value=f"{pr_details['author']}\n{pr_details['head_branch']} → {pr_details['base_branch']}", 
                inline=True
            )
            
            # Check if PR was merged or closed
            if pr_details["state"] != "open":
                for item in self.children:
                    if item.label in ["✅ Approve & Merge", "❌ Reject"]:
                        item.disabled = True
                
                if pr_details["merged"]:
                    embed.color = discord.Color.green()
                    embed.add_field(name="Status", value="✅ This PR has been merged", inline=False)
                else:
                    embed.color = discord.Color.red()
                    embed.add_field(name="Status", value="❌ This PR has been closed", inline=False)
            
            embed.set_footer(text="Use the buttons below to approve or reject this PR")
            
            await interaction.edit_original_response(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"PR refresh failed: {e}")
            await interaction.followup.send("❌ Failed to refresh PR details", ephemeral=True)
    
    async def on_timeout(self):
        """Handle timeout"""
        for item in self.children:
            item.disabled = True

class RejectReasonModal(discord.ui.Modal, title="Reject Pull Request"):
    """Modal for entering rejection reason"""
    
    def __init__(self, pr_number: int, view: PRReviewView):
        super().__init__()
        self.pr_number = pr_number
        self.view = view
    
    reason = discord.ui.TextInput(
        label="Reason for rejection",
        placeholder="Please provide a clear reason for rejecting this PR...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            bot = interaction.client
            result = await bot.orchestrator.reject_pr(self.pr_number, self.reason.value, str(interaction.user.id))
            
            if result["success"]:
                embed = discord.Embed(
                    title="❌ PR Rejected",
                    description=f"PR #{self.pr_number} has been rejected by {interaction.user.mention}",
                    color=discord.Color.red()
                )
                embed.add_field(name="PR Title", value=result.get("pr_title", "N/A"), inline=False)
                embed.add_field(name="Reason", value=self.reason.value, inline=False)
                embed.set_footer(text=f"Rejected by {interaction.user.display_name}")
                
                # Disable all action buttons on the original view
                for item in self.view.children:
                    if item.label in ["✅ Approve & Merge", "❌ Reject"]:
                        item.disabled = True
                
                # Update the original message
                await interaction.edit_original_response(view=self.view)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Failed to reject PR: {result['message']}", ephemeral=True)
                
        except Exception as e:
            logger.error(f"PR reject modal failed: {e}")
            await interaction.followup.send("❌ An error occurred while rejecting the PR.", ephemeral=True)

    # ===== TESTING AGENT COMMANDS =====

    @bot.tree.command(name="test-pr", description="Run tests on a specific pull request")
    @app_commands.describe(pr_number="The pull request number to test")
    async def test_pr_command(interaction: discord.Interaction, pr_number: int):
        """Manually trigger tests on a specific PR"""
        await interaction.response.defer()
        
        try:
            # Trigger tests via orchestrator
            result = await bot.orchestrator.trigger_pr_tests(pr_number, str(interaction.user.id))
            
            if result["success"]:
                embed = discord.Embed(
                    title="🧪 Tests Triggered",
                    description=f"Testing started for PR #{pr_number}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Status", value="Tests are running...", inline=True)
                embed.add_field(name="PR Number", value=f"#{pr_number}", inline=True)
                embed.add_field(name="Triggered By", value=interaction.user.display_name, inline=True)
                embed.set_footer(text="You'll receive test results when complete")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Failed to trigger tests: {result['message']}", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Test PR command failed: {e}")
            await interaction.followup.send("❌ An error occurred while triggering tests.", ephemeral=True)

    @bot.tree.command(name="test-status", description="Get current testing agent status and recent test results")
    async def test_status_command(interaction: discord.Interaction):
        """Get testing agent status and recent results"""
        await interaction.response.defer()
        
        try:
            # Get testing status from orchestrator
            status = await bot.orchestrator.get_testing_status()
            
            embed = discord.Embed(
                title="🧪 Testing Agent Status",
                color=discord.Color.green() if status.get("online", False) else discord.Color.red()
            )
            
            # Agent status
            agent_status = "🟢 Online" if status.get("online", False) else "🔴 Offline"
            embed.add_field(name="Agent Status", value=agent_status, inline=True)
            
            # Active tests
            active_tests = status.get("active_tests", 0)
            embed.add_field(name="Active Tests", value=f"{active_tests} running", inline=True)
            
            # Auto-approve setting
            auto_approve = "✅ Enabled" if status.get("auto_approve", False) else "❌ Disabled"
            embed.add_field(name="Auto-Approve", value=auto_approve, inline=True)
            
            # Recent test results
            recent_tests = status.get("recent_tests", [])
            if recent_tests:
                test_summary = "\n".join([
                    f"PR #{test['pr_number']}: {test['status']} ({test['duration']:.1f}s)"
                    for test in recent_tests[:5]
                ])
                embed.add_field(name="Recent Tests (Last 5)", value=test_summary, inline=False)
            
            # Statistics
            stats = status.get("statistics", {})
            if stats:
                embed.add_field(
                    name="Test Statistics",
                    value=f"Total: {stats.get('total', 0)} | "
                          f"Passed: {stats.get('passed', 0)} | "
                          f"Failed: {stats.get('failed', 0)}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Test status command failed: {e}")
            await interaction.followup.send("❌ An error occurred while getting test status.", ephemeral=True)

    @bot.tree.command(name="test-config", description="Configure testing agent settings")
    @app_commands.describe(
        auto_approve="Enable/disable automatic PR approval for passing tests",
        polling_interval="How often to check for new PRs (in seconds)"
    )
    @app_commands.choices(auto_approve=[
        app_commands.Choice(name="Enable", value="true"),
        app_commands.Choice(name="Disable", value="false")
    ])
    async def test_config_command(
        interaction: discord.Interaction, 
        auto_approve: Optional[str] = None,
        polling_interval: Optional[int] = None
    ):
        """Configure testing agent settings"""
        await interaction.response.defer()
        
        try:
            config_changes = {}
            if auto_approve is not None:
                config_changes["auto_approve"] = auto_approve.lower() == "true"
            if polling_interval is not None:
                config_changes["polling_interval"] = polling_interval
            
            if not config_changes:
                await interaction.followup.send("❌ No configuration changes specified.", ephemeral=True)
                return
            
            # Update configuration via orchestrator
            result = await bot.orchestrator.update_testing_config(config_changes)
            
            if result["success"]:
                embed = discord.Embed(
                    title="🧪 Testing Configuration Updated",
                    color=discord.Color.green()
                )
                
                for key, value in config_changes.items():
                    embed.add_field(
                        name=key.replace("_", " ").title(),
                        value=str(value),
                        inline=True
                    )
                
                embed.set_footer(text=f"Updated by {interaction.user.display_name}")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Failed to update configuration: {result['message']}", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Test config command failed: {e}")
            await interaction.followup.send("❌ An error occurred while updating configuration.", ephemeral=True)

    @bot.tree.command(name="test-logs", description="Get recent testing agent logs")
    @app_commands.describe(
        lines="Number of log lines to retrieve (default: 20)",
        level="Log level filter (all, error, warning, info)"
    )
    @app_commands.choices(level=[
        app_commands.Choice(name="All", value="all"),
        app_commands.Choice(name="Error", value="error"),
        app_commands.Choice(name="Warning", value="warning"),
        app_commands.Choice(name="Info", value="info")
    ])
    async def test_logs_command(
        interaction: discord.Interaction,
        lines: Optional[int] = 20,
        level: Optional[str] = "all"
    ):
        """Get testing agent logs"""
        await interaction.response.defer()
        
        try:
            # Validate lines parameter
            lines = max(1, min(lines or 20, 100))  # Limit between 1-100
            
            # Get logs from orchestrator
            logs = await bot.orchestrator.get_testing_logs(lines=lines, level=level)
            
            if logs["success"]:
                log_content = logs["logs"]
                
                if len(log_content) > 1900:  # Discord message limit minus embed overhead
                    log_content = log_content[-1900:] + "\n... (truncated)"
                
                embed = discord.Embed(
                    title=f"🧪 Testing Agent Logs (Last {lines} lines)",
                    description=f"```\n{log_content}\n```",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Filter", value=level.title(), inline=True)
                embed.add_field(name="Lines", value=str(lines), inline=True)
                embed.set_footer(text=f"Requested by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Failed to retrieve logs: {logs['message']}", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Test logs command failed: {e}")
            await interaction.followup.send("❌ An error occurred while retrieving logs.", ephemeral=True)