# agents/orchestrator/main.py
"""Main entry point for the Orchestrator Agent"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import discord
from discord.ext import commands
from dotenv import load_dotenv

from agents.orchestrator.orchestrator import OrchestratorAgent
from agents.orchestrator.commands import setup_commands
from database.models.base import engine
from database.models.logs import Log, LogLevel
from database.models.agent import Agent, AgentStatus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomationHubBot(commands.Bot):
    """Discord bot for the Automation Hub"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='AI Agent Automation Hub - Your personal development team'
        )
        
        self.orchestrator = None
        
    async def setup_hook(self):
        """Initialize bot components"""
        logger.info("🤖 Setting up Automation Hub Bot...")
        
        # Initialize orchestrator agent
        self.orchestrator = OrchestratorAgent()
        await self.orchestrator.initialize()
        
        # Setup slash commands
        await setup_commands(self)
        
        # Register agent in database
        await self._register_agent()
        
        logger.info("✅ Bot setup completed successfully")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"🚀 {self.user} is now online!")
        logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"⚡ Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")
        
        # Update agent status
        await self._update_agent_status(AgentStatus.ACTIVE)
        
    async def on_error(self, event, *args, **kwargs):
        """Handle bot errors"""
        logger.error(f"❌ Bot error in {event}: {sys.exc_info()}")
        await self.orchestrator.log_error(f"Discord bot error in {event}", sys.exc_info())
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        logger.error(f"❌ Command error: {error}")
        await ctx.send(f"⚠️ An error occurred: {str(error)[:100]}...")
        await self.orchestrator.log_error(f"Command error: {error}", ctx)
    
    async def _register_agent(self):
        """Register orchestrator agent in database"""
        try:
            await self.orchestrator.register_agent()
            logger.info("✅ Orchestrator agent registered in database")
        except Exception as e:
            logger.error(f"❌ Failed to register agent: {e}")
    
    async def _update_agent_status(self, status: AgentStatus):
        """Update agent status in database"""
        try:
            await self.orchestrator.update_status(status)
            logger.info(f"📊 Agent status updated to: {status.value}")
        except Exception as e:
            logger.error(f"❌ Failed to update agent status: {e}")

async def main():
    """Main async entry point"""
    # Validate environment variables
    required_env_vars = ['DISCORD_BOT_TOKEN', 'DATABASE_URL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Initialize bot
    bot = AutomationHubBot()
    
    try:
        # Start the bot
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if not discord_token:
            raise ValueError("DISCORD_BOT_TOKEN not found in environment")
            
        logger.info("🚀 Starting Automation Hub Bot...")
        await bot.start(discord_token)
        
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        sys.exit(1)
    finally:
        if bot.orchestrator:
            await bot.orchestrator.update_status(AgentStatus.OFFLINE)
        await bot.close()
        logger.info("👋 Bot shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot terminated by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)