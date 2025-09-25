#!/usr/bin/env python3
"""
Discord Command Debug Script
Comprehensive troubleshooting for slash command issues
"""
import asyncio
import os
import sys
import discord
from discord.ext import commands
from discord import app_commands

# Add project root to path
sys.path.append(os.path.abspath('.'))

async def debug_discord_commands():
    """Debug Discord slash commands registration"""
    
    print("🔍 Discord Slash Commands Debug Tool")
    print("=" * 50)
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv('DISCORD_BOT_TOKEN')
        
        if not token:
            print("❌ DISCORD_BOT_TOKEN not found in environment!")
            return
        
        print("✅ Bot token loaded")
    except Exception as e:
        print(f"❌ Error loading environment: {e}")
        return
    
    # Initialize bot with intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot connected: {bot.user}")
        print(f"📊 Connected to {len(bot.guilds)} guild(s)")
        
        # List guilds
        for guild in bot.guilds:
            print(f"   🏠 Guild: {guild.name} (ID: {guild.id})")
            
            # Check bot permissions in this guild
            try:
                member = guild.get_member(bot.user.id)
                if member:
                    perms = member.guild_permissions
                    print(f"   🔑 Bot permissions in {guild.name}:")
                    print(f"      - Administrator: {perms.administrator}")
                    print(f"      - Use Application Commands: {perms.use_application_commands}")
                    print(f"      - Send Messages: {perms.send_messages}")
                    print(f"      - Manage Messages: {perms.manage_messages}")
                else:
                    print(f"   ❌ Bot not found as member in {guild.name}")
            except Exception as e:
                print(f"   ❌ Error checking permissions: {e}")
        
        # Check existing slash commands
        print("\n🔍 Checking registered slash commands...")
        try:
            # Global commands
            global_commands = await bot.tree.fetch_commands()
            print(f"📋 Global slash commands: {len(global_commands)}")
            for cmd in global_commands:
                print(f"   - {cmd.name}: {cmd.description}")
            
            # Guild-specific commands for each guild
            for guild in bot.guilds:
                try:
                    guild_commands = await bot.tree.fetch_commands(guild=guild)
                    print(f"📋 Guild commands for {guild.name}: {len(guild_commands)}")
                    for cmd in guild_commands:
                        print(f"   - {cmd.name}: {cmd.description}")
                except Exception as e:
                    print(f"   ❌ Error fetching guild commands for {guild.name}: {e}")
                    
        except Exception as e:
            print(f"❌ Error fetching commands: {e}")
        
        # Test command registration
        print("\n🧪 Testing command registration...")
        
        @bot.tree.command(name="test_debug", description="Test command for debugging")
        async def test_debug(interaction: discord.Interaction):
            await interaction.response.send_message("Debug test successful!", ephemeral=True)
        
        try:
            # Sync commands
            print("🔄 Syncing commands...")
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} command(s)")
            
            # Also try guild-specific sync for each guild
            for guild in bot.guilds:
                try:
                    guild_synced = await bot.tree.sync(guild=guild)
                    print(f"✅ Guild sync for {guild.name}: {len(guild_synced)} commands")
                except Exception as e:
                    print(f"❌ Guild sync error for {guild.name}: {e}")
                    
        except Exception as e:
            print(f"❌ Sync error: {e}")
        
        print("\n📋 Diagnostic Summary:")
        print("1. Check if bot has 'Use Application Commands' permission")
        print("2. Verify bot was invited with applications.commands scope")
        print("3. Wait 5-15 minutes for Discord to propagate slash commands")
        print("4. Try kicking and re-inviting bot if commands still don't appear")
        print("5. In Discord, type '/' to see if commands appear in autocomplete")
        
        # Stop bot after diagnosis
        await bot.close()
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Bot startup error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_discord_commands())