#!/usr/bin/env python3
"""
Discord Bot Integration Example

This script demonstrates how the Discord bot integrates with the specialized
agent system and shows example usage of all bot features.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.main import DiscordBot, setup_bot
from bot.config import BotConfig
from bot.utils import EmbedBuilder, TaskFormatter, PermissionChecker
from agents.orchestrator_agent import OrchestratorAgent
from agents.backend_agent import BackendAgent
from agents.database_agent import DatabaseAgent


def demonstrate_bot_features():
    """Demonstrate the Discord bot features and integration."""
    print("🤖 Discord Bot Integration Demo")
    print("===============================\n")
    
    # 1. Configuration demonstration
    print("1. 📋 Configuration Management")
    print("-" * 30)
    
    try:
        # Check if we can load configuration (will use defaults if no .env)
        os.environ.setdefault('DISCORD_BOT_TOKEN', 'demo_token_123')
        config = BotConfig.from_env()
        validation = config.validate()
        
        print(f"✅ Configuration loaded successfully")
        print(f"⚙️  Max concurrent tasks: {config.max_concurrent_tasks}")
        print(f"🕒 Status update interval: {config.status_update_interval_minutes} minutes")
        print(f"📝 Log level: {config.log_level}")
        
        if validation['warnings']:
            print("⚠️  Configuration warnings:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    print()
    
    # 2. Agent initialization demonstration
    print("2. 🤖 Agent System Integration")
    print("-" * 30)
    
    try:
        orchestrator = OrchestratorAgent("DemoOrchestrator")
        backend = BackendAgent("DemoBackend")
        database = DatabaseAgent("DemoDatabase")
        
        print("✅ Orchestrator Agent initialized")
        print("✅ Backend Agent initialized")
        print("✅ Database Agent initialized")
        
        # Demonstrate agent preparation
        orchestrator.prepare_for_task('Handle task coordination and Discord command parsing', 'pre_task')
        backend.prepare_for_task('Prepare for backend development tasks', 'backend')
        database.prepare_for_task('Prepare for database operations', 'database')
        
        print("🎯 All agents prepared for task execution")
        
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
    
    print()
    
    # 3. Command parsing demonstration
    print("3. 💬 Discord Command Processing")
    print("-" * 30)
    
    try:
        # Simulate Discord commands
        test_commands = [
            "/assign-task Create user authentication API backend",
            "/assign-task Design user database schema database",
            "/assign-task Set up project orchestration orchestration"
        ]
        
        for command in test_commands:
            result = orchestrator.parse_discord_command(command)
            print(f"✅ {command}")
            print(f"   Command Type: {result.get('command_type', 'Unknown')}")
            print(f"   Task Description: {result.get('task_description', 'None')}")
            print(f"   Complexity: {result.get('complexity', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Command parsing error: {e}")
    
    print()
    
    # 4. Task assignment demonstration
    print("4. 📋 Task Assignment System")
    print("-" * 30)
    
    try:
        # Test task breakdown and assignment
        tasks = [
            ("Create REST API for user management", "backend"),
            ("Design normalized database schema", "database"),
            ("Coordinate development workflow", "orchestration")
        ]
        
        for description, task_type in tasks:
            breakdown = orchestrator.break_down_task(description)
            assignment = orchestrator.assign_to_agent(breakdown)
            
            print(f"📝 Task: {description}")
            print(f"   Type: {task_type}")
            print(f"   Assigned to: {assignment['assigned_agent']}")
            print(f"   Subtasks: {len(breakdown)} subtasks")
            print(f"   Next steps: {assignment['next_steps'][:50]}...")
            print()
    
    except Exception as e:
        print(f"❌ Task assignment error: {e}")
    
    # 5. Embed formatting demonstration
    print("5. 🎨 Discord Embed Formatting")
    print("-" * 30)
    
    try:
        # Demonstrate embed creation
        embed_builder = EmbedBuilder()
        
        # Success embed
        success_embed = embed_builder.success(
            "Task Completed",
            "API endpoint created successfully",
            field_endpoint="/api/users",
            field_status="Ready for testing"
        )
        print(f"✅ Success embed: {success_embed.title}")
        
        # Error embed
        error_embed = embed_builder.error(
            "Task Failed",
            "Database connection error",
            error="Connection timeout after 30 seconds"
        )
        print(f"❌ Error embed: {error_embed.title}")
        
        # Task embed
        task_data = {
            'id': 'task_001_20241224_143022',
            'description': 'Create user authentication system',
            'status': 'in_progress',
            'task_type': 'backend',
            'assigned_agent': 'BackendAgent',
            'created_at': datetime.now(),
            'assigned_by': '123456789'
        }
        
        task_embed = TaskFormatter.create_task_embed(task_data)
        print(f"📋 Task embed: {task_embed.title}")
        
    except Exception as e:
        print(f"❌ Embed formatting error: {e}")
    
    print()
    
    # 6. Permission system demonstration
    print("6. 🔐 Permission System")
    print("-" * 30)
    
    try:
        permission_checker = PermissionChecker()
        
        # These would normally be Discord member objects
        # Here we just demonstrate the permission logic
        print("✅ Permission checker initialized")
        print("🔧 Admin permissions: Role-based and permission-based")
        print("📝 Task management: Message management required")
        print("👍 Task approval: Channel management required")
        
    except Exception as e:
        print(f"❌ Permission system error: {e}")
    
    print()
    
    # 7. Bot setup demonstration (without actually running)
    print("7. 🚀 Bot Setup Process")
    print("-" * 30)
    
    try:
        print("🔧 Bot initialization steps:")
        print("   1. Load and validate configuration")
        print("   2. Initialize Discord client with intents")
        print("   3. Set up specialized agents")
        print("   4. Prepare agents for task execution")
        print("   5. Register slash commands")
        print("   6. Start periodic status updates")
        print("   7. Connect to Discord")
        
        print("\n📋 Available slash commands:")
        commands = [
            "/assign-task - Assign tasks to agents",
            "/status - Show agent status",
            "/approve - Approve pull requests", 
            "/agent-logs - View agent logs",
            "/emergency-stop - Emergency halt (admin only)"
        ]
        
        for cmd in commands:
            print(f"   {cmd}")
        
    except Exception as e:
        print(f"❌ Bot setup error: {e}")
    
    print()
    
    # 8. Integration workflow demonstration
    print("8. 🔄 Complete Workflow Example")
    print("-" * 30)
    
    try:
        print("📋 Example workflow:")
        print("   1. User runs: /assign-task 'Create user API' backend")
        print("   2. Bot parses command via OrchestratorAgent")
        print("   3. OrchestratorAgent breaks down task")
        print("   4. Task assigned to BackendAgent")
        print("   5. BackendAgent prepares for backend development")
        print("   6. Task status updated and tracked")
        print("   7. Progress reported every 30 minutes")
        print("   8. User runs: /approve task_123 when ready")
        print("   9. Task marked as completed")
        print("   10. Agent ready for next assignment")
        
        print("\n🔍 Monitoring and control:")
        print("   - /status shows real-time agent status")
        print("   - /agent-logs provides detailed logging")
        print("   - /emergency-stop halts all activity")
        print("   - Periodic status updates to monitoring channel")
        
    except Exception as e:
        print(f"❌ Workflow demonstration error: {e}")
    
    print()
    print("✨ Discord bot demonstration completed!")
    print("🚀 Ready for deployment with proper Discord token")


async def test_async_functionality():
    """Test async functionality of the bot components."""
    print("\n🔄 Testing Async Functionality")
    print("=" * 30)
    
    try:
        from bot.utils import AsyncCache, RateLimiter, safe_send
        
        # Test async cache
        print("📦 Testing async cache...")
        cache = AsyncCache(default_ttl=60)
        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        print(f"   Cache test: {value == 'test_value'}")
        
        # Test rate limiter
        print("⏱️  Testing rate limiter...")
        limiter = RateLimiter(max_calls=5, window_seconds=60)
        user_id = 12345
        
        # Should allow first few calls
        allowed_calls = 0
        for i in range(10):
            if limiter.is_allowed(user_id):
                allowed_calls += 1
        
        print(f"   Rate limiter test: {allowed_calls <= 5}")
        
        print("✅ Async functionality tests completed")
        
    except Exception as e:
        print(f"❌ Async test error: {e}")


def main():
    """Main demonstration function."""
    # Run synchronous demonstrations
    demonstrate_bot_features()
    
    # Run async demonstrations
    try:
        asyncio.run(test_async_functionality())
    except Exception as e:
        print(f"❌ Async demonstration error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Discord Bot Setup Instructions")
    print("=" * 50)
    print()
    print("1. 🔑 Get Discord Bot Token:")
    print("   - Go to https://discord.com/developers/applications")
    print("   - Create new application")
    print("   - Go to 'Bot' section")
    print("   - Create bot and copy token")
    print()
    print("2. 📝 Configure Environment:")
    print("   - Copy .env.bot.template to .env")
    print("   - Set DISCORD_BOT_TOKEN=your_token")
    print("   - Configure optional settings")
    print()
    print("3. 🚀 Start Bot:")
    print("   - Run: python bot/run_bot.py")
    print("   - Or use: ./bot/run_bot.py")
    print()
    print("4. 🔗 Invite Bot to Server:")
    print("   - Use Discord Developer Portal")
    print("   - Select bot permissions")
    print("   - Generate invite link")
    print()
    print("5. ✅ Test Commands:")
    print("   - Use /assign-task in your Discord server")
    print("   - Try /status to see agent status")
    print("   - Check logs for debugging")


if __name__ == "__main__":
    main()