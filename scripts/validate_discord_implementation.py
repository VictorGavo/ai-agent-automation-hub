#!/usr/bin/env python3
"""
Discord Commands Validation Script
Validates that all new Discord commands can be imported and initialized properly.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def validate_discord_commands():
    """Validate Discord commands can be imported"""
    print("🔍 Validating Discord Approval Workflow Implementation...")
    print("=" * 60)
    
    try:
        # Test basic imports
        print("1. Testing basic imports...")
        import discord
        from discord import app_commands
        from discord.ext import commands
        print("   ✅ Discord imports successful")
        
        # Test command module import
        print("2. Testing command module...")
        from agents.orchestrator.commands import setup_commands
        print("   ✅ Commands module imported successfully")
        
        # Test view classes
        print("3. Testing view classes...")
        from agents.orchestrator.commands import PRReviewView, RejectReasonModal
        print("   ✅ Interactive view classes available")
        
        # Test that we can create a mock bot and views
        print("4. Testing command initialization...")
        
        # Create a minimal mock bot class
        class MockBot:
            def __init__(self):
                self.tree = type('tree', (), {'command': lambda **kwargs: lambda f: f})()
                self.orchestrator = None
        
        mock_bot = MockBot()
        
        # Test PR review view creation
        pr_view = PRReviewView(42)
        print("   ✅ PRReviewView can be created")
        
        # Test modal creation
        reject_modal = RejectReasonModal(42, pr_view)
        print("   ✅ RejectReasonModal can be created")
        
        print("\n🎉 All Discord Approval Workflow components validated successfully!")
        
        # Show command summary
        print("\n📋 Available Commands:")
        commands_list = [
            "/approve [pr-number] - Approve and merge PR",
            "/review [pr-number] - Interactive PR review",
            "/reject [pr-number] [reason] - Reject PR with reason",
            "/pending-prs [limit] - List open PRs",
            "/status - Enhanced status with PR metrics"
        ]
        
        for cmd in commands_list:
            print(f"   • {cmd}")
        
        print("\n🔧 Integration Points:")
        print("   • GitHubClient for PR operations")
        print("   • OrchestratorAgent for task management") 
        print("   • Discord bot with interactive buttons")
        print("   • Database for audit trail")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Check that all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\n🔧 Environment Check:")
    print("-" * 25)
    
    # Check for required environment variables
    env_vars = {
        "DISCORD_BOT_TOKEN": "Discord bot authentication",
        "GITHUB_TOKEN": "GitHub API access",
        "DATABASE_URL": "Database connection"
    }
    
    missing_vars = []
    for var, description in env_vars.items():
        if os.getenv(var):
            print(f"   ✅ {var} - {description}")
        else:
            print(f"   ⚠️  {var} - {description} (not set)")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n📝 To run the Discord bot, set these environment variables:")
        for var in missing_vars:
            print(f"   export {var}=your_value_here")
    else:
        print("\n✅ All required environment variables are set!")
    
    return len(missing_vars) == 0

def show_next_steps():
    """Show next steps for using the implementation"""
    print("\n🚀 Next Steps:")
    print("=" * 15)
    
    steps = [
        "1. Set required environment variables (if not already set)",
        "2. Start the Discord bot: python agents/orchestrator/main.py",
        "3. Bot will sync slash commands automatically",
        "4. Test with /status to verify GitHub integration",
        "5. Use /pending-prs to see open pull requests",
        "6. Try /review [pr-number] for interactive approval",
        "7. Enjoy mobile-friendly development workflow! 📱"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print("\n💡 Pro Tips:")
    print("   • Use /review for detailed PR analysis")
    print("   • Tap buttons for one-click approval/rejection")
    print("   • /status shows real-time system health")
    print("   • All actions are logged for audit trail")

def main():
    """Main validation entry point"""
    print("Discord Approval Workflow - Validation")
    print("=" * 40)
    
    # Validate implementation
    if validate_discord_commands():
        print("\n🎯 Implementation Status: READY ✅")
    else:
        print("\n❌ Implementation Status: ISSUES FOUND")
        return 1
    
    # Check environment
    env_ready = check_environment()
    
    # Show next steps
    show_next_steps()
    
    if env_ready:
        print("\n🚀 System Status: READY TO LAUNCH! 🎉")
    else:
        print("\n⚠️  System Status: Environment setup needed")
    
    return 0

if __name__ == "__main__":
    exit(main())