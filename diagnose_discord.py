#!/usr/bin/env python3
"""
Discord Bot Diagnostic Tool

This script helps diagnose Discord slash command issues by checking:
- Bot permissions
- Guild information
- Command registration status
- Potential fixes
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Load environment
load_dotenv()

async def diagnose_discord_bot():
    """Run comprehensive Discord bot diagnostics."""
    
    print("🔍 Discord Bot Diagnostics")
    print("=" * 50)
    
    # Check token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found in .env file")
        return
    
    print(f"✅ Bot token configured: {token[:10]}...{token[-10:]}")
    
    # Create bot for diagnostics
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"\n🤖 Bot Information:")
        print(f"   Name: {bot.user.name}")
        print(f"   ID: {bot.user.id}")
        print(f"   Guilds: {len(bot.guilds)}")
        
        if bot.guilds:
            for guild in bot.guilds:
                print(f"\n🏰 Guild: {guild.name} (ID: {guild.id})")
                print(f"   Members: {guild.member_count}")
                
                # Check bot permissions in guild
                bot_member = guild.get_member(bot.user.id)
                if bot_member:
                    perms = bot_member.guild_permissions
                    print(f"   📋 Bot Permissions:")
                    print(f"      Administrator: {perms.administrator}")
                    print(f"      Use Slash Commands: {perms.use_slash_commands}")
                    print(f"      Send Messages: {perms.send_messages}")
                    print(f"      Embed Links: {perms.embed_links}")
                    print(f"      Manage Messages: {perms.manage_messages}")
                    
                    # Check if bot can use slash commands in each channel
                    text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
                    print(f"   📺 Text Channels: {len(text_channels)}")
                    
                    for channel in text_channels[:5]:  # Check first 5 channels
                        channel_perms = channel.permissions_for(bot_member)
                        can_use_slash = (
                            channel_perms.send_messages and 
                            channel_perms.use_slash_commands and 
                            channel_perms.embed_links
                        )
                        status = "✅" if can_use_slash else "❌"
                        print(f"      {status} #{channel.name}: Slash commands {'enabled' if can_use_slash else 'disabled'}")
        
        # Check global commands
        try:
            global_commands = await bot.tree.fetch_commands()
            print(f"\n📝 Global Slash Commands: {len(global_commands)}")
            for cmd in global_commands:
                print(f"   - /{cmd.name}: {cmd.description}")
        except Exception as e:
            print(f"\n❌ Error fetching global commands: {e}")
        
        # Check guild-specific commands for each guild
        for guild in bot.guilds:
            try:
                guild_commands = await bot.tree.fetch_commands(guild=guild)
                print(f"\n📝 Guild Commands for {guild.name}: {len(guild_commands)}")
                for cmd in guild_commands:
                    print(f"   - /{cmd.name}: {cmd.description}")
            except Exception as e:
                print(f"\n❌ Error fetching guild commands for {guild.name}: {e}")
        
        # Provide recommendations
        print("\n💡 Troubleshooting Recommendations:")
        
        if not bot.guilds:
            print("   ❌ Bot is not in any servers")
            print("   🔧 Solution: Re-invite bot with proper permissions")
            print("   🔗 Use this URL format:")
            print(f"   https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=2147483647&scope=bot%20applications.commands")
        
        else:
            for guild in bot.guilds:
                bot_member = guild.get_member(bot.user.id)
                if bot_member:
                    perms = bot_member.guild_permissions
                    
                    if not perms.use_slash_commands:
                        print(f"   ❌ Bot missing 'Use Slash Commands' permission in {guild.name}")
                        print("   🔧 Solution: Grant 'Use Application Commands' permission")
                    
                    if not perms.send_messages:
                        print(f"   ❌ Bot missing 'Send Messages' permission in {guild.name}")
                        print("   🔧 Solution: Grant 'Send Messages' permission")
                    
                    if not perms.embed_links:
                        print(f"   ❌ Bot missing 'Embed Links' permission in {guild.name}")
                        print("   🔧 Solution: Grant 'Embed Links' permission")
        
        print("\n⏰ Command Sync Timing:")
        print("   - Global commands: Can take up to 1 hour to appear")
        print("   - Guild commands: Should appear within 5-10 minutes")
        print("   - Try refreshing Discord app (Ctrl+Shift+R or restart)")
        
        print("\n🔄 Force Command Sync:")
        try:
            # Force sync commands
            synced = await bot.tree.sync()
            print(f"   ✅ Synced {len(synced)} global commands")
            
            # Sync to each guild
            for guild in bot.guilds:
                try:
                    guild_synced = await bot.tree.sync(guild=guild)
                    print(f"   ✅ Synced {len(guild_synced)} commands to {guild.name}")
                except Exception as e:
                    print(f"   ❌ Failed to sync to {guild.name}: {e}")
                    
        except Exception as e:
            print(f"   ❌ Failed to sync commands: {e}")
        
        print("\n✅ Diagnostics Complete!")
        await bot.close()
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    print("Starting Discord Bot Diagnostics...")
    asyncio.run(diagnose_discord_bot())