#!/usr/bin/env python3
"""
Simple Discord Bot - Debug Version

Minimal implementation to test slash command registration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleBot(discord.Client):
    """
    Very simple Discord bot to test command registration.
    """
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.setup_commands()
    
    def setup_commands(self):
        """Setup slash commands."""
        
        @self.tree.command(name="ping", description="Test command")
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message("🏓 Pong!")
            logger.info(f"Ping used by {interaction.user}")
        
        @self.tree.command(name="status", description="Show bot status")
        async def status(interaction: discord.Interaction):
            embed = discord.Embed(title="🤖 Bot Status", color=discord.Color.green())
            embed.add_field(name="Status", value="✅ Online", inline=False)
            await interaction.response.send_message(embed=embed)
            logger.info(f"Status used by {interaction.user}")
        
        @self.tree.command(name="assign-task", description="Assign a task")
        @app_commands.describe(
            description="Task description",
            task_type="Task type (backend, database, testing)"
        )
        async def assign_task(interaction: discord.Interaction, description: str, task_type: str):
            embed = discord.Embed(title="✅ Task Assigned", color=discord.Color.blue())
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Type", value=task_type, inline=True)
            await interaction.response.send_message(embed=embed)
            logger.info(f"Task assigned by {interaction.user}: {description}")
        
        logger.info("Commands setup complete")
    
    async def setup_hook(self):
        """Setup hook called when bot starts."""
        try:
            # Debug: Show what commands are in the tree before syncing
            commands = self.tree.get_commands()
            logger.info(f"DEBUG: Commands in tree: {len(commands)}")
            for cmd in commands:
                logger.info(f"  - {cmd.name}: {cmd.description}")
            
            guild_id = os.getenv('DISCORD_GUILD_ID')
            
            # Force global sync for testing
            guild_id = None
            
            if guild_id:
                # Sync to specific guild for faster testing
                guild = discord.Object(id=int(guild_id))
                synced = await self.tree.sync(guild=guild)
                logger.info(f"✅ Synced {len(synced)} commands to guild {guild_id}")
                
                for cmd in synced:
                    logger.info(f"  - /{cmd.name}: {cmd.description}")
            else:
                # Sync globally
                synced = await self.tree.sync()
                logger.info(f"✅ Synced {len(synced)} commands globally")
                
                for cmd in synced:
                    logger.info(f"  - /{cmd.name}: {cmd.description}")
                
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
            raise
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info("=" * 50)
        logger.info(f"🤖 Bot ready: {self.user} (ID: {self.user.id})")
        logger.info(f"📊 Guilds: {len(self.guilds)}")
        
        for guild in self.guilds:
            logger.info(f"  - {guild.name} (ID: {guild.id})")
        
        # Set activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for /assign-task"
        )
        await self.change_presence(activity=activity)
        
        logger.info("✅ Bot is fully ready!")
        logger.info("=" * 50)


async def main():
    """Main function."""
    try:
        # Validate token
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN not found in environment")
        
        guild_id = None  # Force global sync for testing
        logger.warning("Testing with global sync (guild sync disabled)")
        
        # Create and run bot
        bot = SimpleBot()
        
        logger.info("Starting simple Discord bot...")
        async with bot:
            await bot.start(token)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        logger.info("Bot shutdown")


if __name__ == "__main__":
    asyncio.run(main())