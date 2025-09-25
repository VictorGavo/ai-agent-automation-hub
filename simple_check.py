#!/usr/bin/env python3
"""
Simple Discord Slash Command Checker
"""
import os
import asyncio
import discord
from discord.ext import commands

async def check_commands():
    """Check Discord bot command registration status"""
    
    print("🔍 Discord Command Status Checker")
    print("=" * 40)
    
    # Load token
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("❌ No bot token found!")
        return
    
    # Create minimal bot
    intents = discord.Intents.default()
    intents.guilds = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Connected as: {bot.user}")
        print(f"📊 Guilds: {len(bot.guilds)}")
        
        for guild in bot.guilds:
            print(f"\n🏠 Guild: {guild.name} (ID: {guild.id})")
            
            # Check permissions
            me = guild.me
            if me:
                perms = me.guild_permissions
                print(f"🔑 Permissions:")
                print(f"   - Administrator: {perms.administrator}")
                print(f"   - Use App Commands: {perms.use_application_commands}")
                print(f"   - Send Messages: {perms.send_messages}")
            
            # Check commands
            try:
                commands_list = await bot.tree.fetch_commands(guild=guild)
                print(f"📋 Registered commands: {len(commands_list)}")
                for cmd in commands_list:
                    print(f"   - /{cmd.name}")
            except Exception as e:
                print(f"❌ Error fetching commands: {e}")
        
        # Check global commands
        try:
            global_commands = await bot.tree.fetch_commands()
            print(f"\n🌍 Global commands: {len(global_commands)}")
            for cmd in global_commands:
                print(f"   - /{cmd.name}")
        except Exception as e:
            print(f"❌ Error fetching global commands: {e}")
        
        await bot.close()
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(check_commands())