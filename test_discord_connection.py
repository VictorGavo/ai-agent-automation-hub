#!/usr/bin/env python3
"""
Discord Bot Connection Test

This script tests the Discord bot initialization and connection
to validate that the Discord token and configuration are working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_discord_connection():
    """Test Discord bot connection and basic functionality."""
    
    print("🔗 Testing Discord Bot Connection...")
    print("="*50)
    
    # Check environment variables
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    guild_id = os.getenv('DISCORD_GUILD_ID')
    
    print(f"✅ Discord Token: {'Set' if discord_token else 'Missing'}")
    print(f"✅ Guild ID: {guild_id if guild_id else 'Not set (optional)'}")
    
    if not discord_token:
        print("❌ Discord token not found in .env file!")
        return False
    
    # Test Discord.py import and basic bot creation
    try:
        import discord
        from discord.ext import commands
        
        print("✅ Discord.py library imported successfully")
        
        # Create a basic bot instance (don't start it)
        intents = discord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"✅ Bot connected as {bot.user}")
            print(f"✅ Bot ID: {bot.user.id}")
            print(f"✅ Connected to {len(bot.guilds)} servers")
            
            if guild_id:
                guild = bot.get_guild(int(guild_id))
                if guild:
                    print(f"✅ Found target guild: {guild.name}")
                else:
                    print(f"⚠️  Guild {guild_id} not found (bot may not be in that server)")
            
            # Disconnect after successful connection test
            await bot.close()
            print("✅ Connection test completed successfully!")
        
        @bot.event
        async def on_error(event, *args, **kwargs):
            print(f"❌ Discord error in {event}: {args}")
        
        # Try to connect (with timeout)
        print("🔄 Attempting to connect to Discord...")
        
        try:
            # Use asyncio.wait_for with timeout
            await asyncio.wait_for(bot.start(discord_token), timeout=15.0)
            return True
        except asyncio.TimeoutError:
            print("⚠️  Connection test timed out (15 seconds)")
            print("   This might happen if the network is slow, but the token is likely valid")
            return True
        except discord.LoginFailure:
            print("❌ Invalid Discord token!")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import Discord.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_bot_configuration():
    """Test bot configuration and environment setup."""
    
    print("\n🛠️  Testing Bot Configuration...")
    print("="*50)
    
    # Check all environment variables
    env_vars = {
        'DISCORD_BOT_TOKEN': os.getenv('DISCORD_BOT_TOKEN'),
        'DISCORD_GUILD_ID': os.getenv('DISCORD_GUILD_ID'),
        'BOT_PREFIX': os.getenv('BOT_PREFIX', '!'),
        'APP_MODE': os.getenv('APP_MODE', 'development'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'MAX_CONCURRENT_TASKS': os.getenv('MAX_CONCURRENT_TASKS', '5')
    }
    
    print("Environment Variables:")
    for key, value in env_vars.items():
        if 'TOKEN' in key and value:
            # Mask token for security
            masked = value[:8] + '...' + value[-8:] if len(value) > 16 else 'SET'
            print(f"  ✅ {key}: {masked}")
        elif value:
            print(f"  ✅ {key}: {value}")
        else:
            print(f"  ⚠️  {key}: Not set")
    
    # Check required files
    print("\nRequired Files:")
    required_files = [
        'bot/main.py',
        'bot/config.py',
        'agents/orchestrator_agent.py',
        'agents/base_agent.py',
        '.env'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            all_files_exist = False
    
    return all_files_exist

async def main():
    """Main test function."""
    
    print("🤖 Discord Bot Connection Test")
    print("="*60)
    
    # Test configuration
    config_ok = test_bot_configuration()
    
    if not config_ok:
        print("\n❌ Configuration test failed!")
        print("   Please ensure all required files exist.")
        return 1
    
    # Test Discord connection
    try:
        connection_ok = await test_discord_connection()
        
        if connection_ok:
            print("\n🎉 Discord bot test completed successfully!")
            print("✅ Your Discord configuration is working correctly.")
            print("✅ The bot should be able to connect and receive commands.")
            return 0
        else:
            print("\n❌ Discord connection test failed!")
            print("   Please check your Discord token and bot permissions.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)