#!/usr/bin/env python3
"""
Discord Bot Startup Script

This script starts the Discord bot with proper error handling and logging setup.
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.main import main as bot_main
from bot.config import get_config


def setup_logging() -> None:
    """Set up logging configuration."""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/discord_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set Discord logging level
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main() -> None:
    """Main entry point for the bot."""
    print("🤖 AI Agent Automation Hub Discord Bot")
    print("======================================")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Load and validate configuration
        logger.info("Loading configuration...")
        config = get_config()
        validation = config.validate()
        
        if not validation['valid']:
            logger.error("Configuration validation failed:")
            for issue in validation['issues']:
                logger.error(f"  - {issue}")
            sys.exit(1)
        
        if validation['warnings']:
            logger.warning("Configuration warnings:")
            for warning in validation['warnings']:
                logger.warning(f"  - {warning}")
        
        logger.info("Configuration loaded successfully")
        
        # Print startup info
        print(f"✅ Configuration loaded")
        print(f"⚠️  Warnings: {len(validation['warnings'])}")
        print(f"🔧 Max concurrent tasks: {config.max_concurrent_tasks}")
        print(f"⏱️  Status update interval: {config.status_update_interval_minutes} minutes")
        print(f"📝 Log level: {config.log_level}")
        print()
        
        # Start the bot
        logger.info("Starting Discord bot...")
        print("🚀 Starting bot...")
        
        asyncio.run(bot_main())
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user (Ctrl+C)")
        print("\n👋 Bot shutdown by user")
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()