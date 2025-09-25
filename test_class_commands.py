#!/usr/bin/env python3
"""
Test the main bot command structure
"""
import os
import asyncio
import discord
from discord.ext import commands

class TestBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents)
    
    @discord.app_commands.command(name="test-status", description="Test status command")
    async def test_status(self, interaction: discord.Interaction):
        await interaction.response.send_message("Status: Working!", ephemeral=True)
    
    @discord.app_commands.command(name="test-ping", description="Test ping command") 
    async def test_ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!", ephemeral=True)
    
    async def setup_hook(self):
        """Called when the bot is starting up"""
        print("Setting up bot...")
        
        # Sync to guild
        guild_id = 1418211809319718984
        guild = discord.Object(id=guild_id)
        
        synced = await self.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild")
        
        await self.close()

async def test_class_commands():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    bot = TestBot()
    
    @bot.event
    async def on_ready():
        print(f"Bot ready: {bot.user}")
    
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(test_class_commands())