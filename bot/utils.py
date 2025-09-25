"""
Discord Bot Utilities

This module provides utility functions and helpers for the Discord bot,
including embed creation, permission checking, and data formatting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class EmbedBuilder:
    """Helper class for creating Discord embeds with consistent styling."""
    
    @staticmethod
    def success(title: str, description: str = "", **kwargs) -> discord.Embed:
        """Create a success embed with green color."""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        for key, value in kwargs.items():
            if key.startswith('field_'):
                # Handle field additions
                field_name = key.replace('field_', '').replace('_', ' ').title()
                embed.add_field(name=field_name, value=value, inline=False)
        
        return embed
    
    @staticmethod
    def error(title: str, description: str = "", error: Optional[str] = None) -> discord.Embed:
        """Create an error embed with red color."""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        if error:
            embed.add_field(
                name="Error Details",
                value=f"```{error[:1000]}```",
                inline=False
            )
        
        return embed
    
    @staticmethod
    def info(title: str, description: str = "", **kwargs) -> discord.Embed:
        """Create an info embed with blue color."""
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for key, value in kwargs.items():
            if key.startswith('field_'):
                field_name = key.replace('field_', '').replace('_', ' ').title()
                embed.add_field(name=field_name, value=value, inline=False)
        
        return embed
    
    @staticmethod
    def warning(title: str, description: str = "", **kwargs) -> discord.Embed:
        """Create a warning embed with orange color."""
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        for key, value in kwargs.items():
            if key.startswith('field_'):
                field_name = key.replace('field_', '').replace('_', ' ').title()
                embed.add_field(name=field_name, value=value, inline=False)
        
        return embed


class PermissionChecker:
    """Helper class for checking user permissions."""
    
    @staticmethod
    def is_admin(member: discord.Member, admin_role_name: str = "Admin") -> bool:
        """Check if a member has admin permissions."""
        # Check if user has administrator permission
        if member.guild_permissions.administrator:
            return True
        
        # Check if user has the admin role
        admin_role = discord.utils.get(member.roles, name=admin_role_name)
        return admin_role is not None
    
    @staticmethod
    def can_manage_tasks(member: discord.Member) -> bool:
        """Check if a member can manage tasks."""
        return (
            member.guild_permissions.manage_messages or
            member.guild_permissions.administrator
        )
    
    @staticmethod
    def can_approve_tasks(member: discord.Member) -> bool:
        """Check if a member can approve tasks."""
        return (
            member.guild_permissions.manage_channels or
            member.guild_permissions.administrator
        )


class TaskFormatter:
    """Helper class for formatting task information."""
    
    @staticmethod
    def format_task_id(task_id: str) -> str:
        """Format a task ID for display."""
        return f"`{task_id}`"
    
    @staticmethod
    def format_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
        """Format task duration."""
        end = end_time or datetime.now()
        duration = end - start_time
        
        if duration.days > 0:
            return f"{duration.days}d {duration.seconds // 3600}h"
        elif duration.seconds >= 3600:
            return f"{duration.seconds // 3600}h {(duration.seconds % 3600) // 60}m"
        elif duration.seconds >= 60:
            return f"{duration.seconds // 60}m {duration.seconds % 60}s"
        else:
            return f"{duration.seconds}s"
    
    @staticmethod
    def format_task_status(status: str) -> str:
        """Format task status with appropriate emoji."""
        status_emojis = {
            'assigned': '📋',
            'in_progress': '⚡',
            'completed': '✅',
            'approved': '👍',
            'rejected': '❌',
            'cancelled': '⏹️',
            'error': '🔥',
            'waiting': '⏳'
        }
        
        emoji = status_emojis.get(status.lower(), '❓')
        return f"{emoji} {status.title()}"
    
    @staticmethod
    def create_task_embed(task_data: Dict[str, Any]) -> discord.Embed:
        """Create a comprehensive task embed."""
        task_id = task_data.get('id', 'unknown')
        description = task_data.get('description', 'No description')
        status = task_data.get('status', 'unknown')
        
        # Choose embed color based on status
        color_map = {
            'assigned': discord.Color.blue(),
            'in_progress': discord.Color.yellow(),
            'completed': discord.Color.green(),
            'approved': discord.Color.green(),
            'rejected': discord.Color.red(),
            'cancelled': discord.Color.dark_grey(),
            'error': discord.Color.red()
        }
        
        color = color_map.get(status.lower(), discord.Color.light_grey())
        
        embed = discord.Embed(
            title=f"Task {TaskFormatter.format_task_id(task_id)}",
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        
        # Add task fields
        embed.add_field(
            name="Status",
            value=TaskFormatter.format_task_status(status),
            inline=True
        )
        
        if 'task_type' in task_data:
            embed.add_field(
                name="Type",
                value=task_data['task_type'].title(),
                inline=True
            )
        
        if 'assigned_agent' in task_data:
            embed.add_field(
                name="Assigned Agent",
                value=task_data['assigned_agent'],
                inline=True
            )
        
        if 'created_at' in task_data:
            created_at = task_data['created_at']
            if isinstance(created_at, datetime):
                embed.add_field(
                    name="Created",
                    value=created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    inline=True
                )
        
        if 'assigned_by' in task_data:
            embed.add_field(
                name="Assigned By",
                value=f"<@{task_data['assigned_by']}>",
                inline=True
            )
        
        # Add duration if applicable
        if 'created_at' in task_data and isinstance(task_data['created_at'], datetime):
            duration = TaskFormatter.format_duration(task_data['created_at'])
            embed.add_field(
                name="Duration",
                value=duration,
                inline=True
            )
        
        return embed


class AsyncCache:
    """Simple async cache for storing temporary data."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a cache value with optional TTL."""
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            'value': value,
            'expiry': expiry
        }
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a cache value, returning default if not found or expired."""
        if key not in self.cache:
            return default
        
        entry = self.cache[key]
        if datetime.now() > entry['expiry']:
            del self.cache[key]
            return default
        
        return entry['value']
    
    async def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear_expired(self) -> int:
        """Clear expired entries and return count of cleared items."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry['expiry']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


class RateLimiter:
    """Simple rate limiter for Discord commands."""
    
    def __init__(self, max_calls: int = 5, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: Dict[int, List[datetime]] = {}
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed to make a call."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old calls
        if user_id in self.calls:
            self.calls[user_id] = [
                call_time for call_time in self.calls[user_id]
                if call_time > window_start
            ]
        else:
            self.calls[user_id] = []
        
        # Check if under limit
        if len(self.calls[user_id]) < self.max_calls:
            self.calls[user_id].append(now)
            return True
        
        return False
    
    def get_reset_time(self, user_id: int) -> Optional[datetime]:
        """Get when the rate limit resets for a user."""
        if user_id not in self.calls or not self.calls[user_id]:
            return None
        
        oldest_call = min(self.calls[user_id])
        return oldest_call + timedelta(seconds=self.window_seconds)


async def safe_send(
    destination: Union[discord.TextChannel, discord.User, discord.Interaction],
    content: str = None,
    embed: discord.Embed = None,
    **kwargs
) -> Optional[discord.Message]:
    """Safely send a message, handling common errors."""
    try:
        if isinstance(destination, discord.Interaction):
            if destination.response.is_done():
                return await destination.followup.send(content=content, embed=embed, **kwargs)
            else:
                await destination.response.send_message(content=content, embed=embed, **kwargs)
                return await destination.original_response()
        else:
            return await destination.send(content=content, embed=embed, **kwargs)
    
    except discord.Forbidden:
        logger.warning(f"No permission to send message to {destination}")
    except discord.HTTPException as e:
        logger.error(f"HTTP error sending message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
    
    return None


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to fit within Discord limits."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_code_block(code: str, language: str = "") -> str:
    """Format code in a Discord code block."""
    # Ensure code doesn't break out of code block
    escaped_code = code.replace("```", "`​`​`")  # Use zero-width spaces
    return f"```{language}\n{escaped_code}\n```"


class PaginatedView(discord.ui.View):
    """A view for paginated content in Discord embeds."""
    
    def __init__(self, embeds: List[discord.Embed], timeout: int = 300):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.max_pages = len(embeds)
        
        # Disable buttons if only one page
        if self.max_pages <= 1:
            self.previous_button.disabled = True
            self.next_button.disabled = True
    
    @discord.ui.button(label='◀️ Previous', style=discord.ButtonStyle.blurple)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label='▶️ Next', style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page."""
        if self.current_page < self.max_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label='🔢 Page Info', style=discord.ButtonStyle.grey)
    async def page_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show page information."""
        await interaction.response.send_message(
            f"Page {self.current_page + 1} of {self.max_pages}",
            ephemeral=True
        )


# Global instances
embed_builder = EmbedBuilder()
permission_checker = PermissionChecker()
task_formatter = TaskFormatter()
async_cache = AsyncCache()

# Rate limiters for different command types
command_rate_limiter = RateLimiter(max_calls=10, window_seconds=60)
admin_rate_limiter = RateLimiter(max_calls=20, window_seconds=60)