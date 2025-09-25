#!/usr/bin/env python3
"""
Basic slash command test
"""
import os
import asyncio
import discord
from discord.ext import commands

async def test_basic_command():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    GUILD_ID = 1418211809319718984
    
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"Bot ready: {bot.user}")
        
        # Add command directly to tree
        @bot.tree.command(guild=discord.Object(id=GUILD_ID))
        async def test(interaction: discord.Interaction):
            """A simple test command"""
            await interaction.response.send_message("Test successful!")
        
        # Try to sync
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands")
        
        await bot.close()
    
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(test_basic_command())