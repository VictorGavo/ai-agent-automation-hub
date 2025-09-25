#!/usr/bin/env python3
"""
Guild-specific command sync for immediate testing
"""
import os
import asyncio
import discord
from discord.ext import commands

async def sync_to_guild():
    """Sync commands to specific guild for immediate availability"""
    
    print("🔄 Guild Command Sync Tool")
    print("=" * 30)
    
    # Load token
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("❌ No bot token found!")
        return
    
    # Your guild ID (from the diagnostic)
    GUILD_ID = 1418211809319718984
    
    intents = discord.Intents.default()
    intents.guilds = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    # Define simple test commands first
    @bot.tree.command(name="status", description="Check system status")
    async def status_command(interaction: discord.Interaction):
        await interaction.response.send_message("✅ Status: Bot is working and commands are synced!", ephemeral=True)
    
    @bot.tree.command(name="ping", description="Test bot response")
    async def ping_command(interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong! Commands are working!", ephemeral=True)
    
    @bot.event
    async def on_ready():
        print(f"✅ Connected as: {bot.user}")
        
        guild = discord.Object(id=GUILD_ID)
        
        try:
            # Clear existing commands in guild first
            bot.tree.clear_commands(guild=guild)
            print("🗑️  Cleared existing guild commands")
            
            # Sync to specific guild (immediate)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} commands to guild")
            print("Commands synced:")
            for cmd in synced:
                print(f"   - /{cmd.name}")
            
            print("\n🎉 Success! Commands should now appear immediately in Discord!")
            print("💡 Try typing '/' in your Discord server to see the commands.")
            
        except Exception as e:
            print(f"❌ Sync error: {e}")
        
        await bot.close()
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(sync_to_guild())