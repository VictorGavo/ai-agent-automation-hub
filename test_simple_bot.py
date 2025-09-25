#!/usr/bin/env python3
"""
Simple Discord Bot Test for Slash Commands

This is a minimal bot to test if slash commands work in your server.
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Create bot with minimal setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.tree.command(name='hello', description='Simple test command')
async def hello(interaction: discord.Interaction):
    """Simple test slash command."""
    await interaction.response.send_message(f'Hello {interaction.user.mention}! 👋')

@bot.tree.command(name='ping', description='Check bot response time')
async def ping(interaction: discord.Interaction):
    """Ping command to test bot responsiveness."""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')

@bot.tree.command(name='test', description='Test if slash commands are working')
async def test(interaction: discord.Interaction):
    """Test command to verify slash command functionality."""
    embed = discord.Embed(
        title="✅ Slash Commands Working!",
        description="This confirms that slash commands are properly registered and working in your server.",
        color=discord.Color.green()
    )
    embed.add_field(name="User", value=interaction.user.mention, inline=True)
    embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
    embed.add_field(name="Server", value=interaction.guild.name if interaction.guild else "DM", inline=True)
    
    await interaction.response.send_message(embed=embed)

if __name__ == '__main__':
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found in .env file!")
    else:
        print("🚀 Starting simple test bot...")
        bot.run(token)