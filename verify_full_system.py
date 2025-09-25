#!/usr/bin/env python3
"""
AI Agent Automation Hub - Full System Verification Script

This script verifies that the complete system is restored and functioning properly:
1. Environment variables are correctly configured
2. Full command set is available in Discord bot
3. Agent integration is working
4. Database connections are functional

Run this script to confirm system health after cleanup.
"""

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Any
import sqlite3

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import discord
from discord import app_commands

# Configure logging for verification
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemVerifier:
    """System verification class to test all components."""
    
    def __init__(self):
        self.results = {}
        self.issues = []
        
    def log_result(self, test_name: str, success: bool, message: str = "", details: Any = None):
        """Log a verification result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results[test_name] = {
            'success': success,
            'message': message,
            'details': details
        }
        
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        if not success:
            self.issues.append(f"{test_name}: {message}")
    
    async def verify_environment_variables(self) -> None:
        """Verify all environment variables are correctly configured."""
        print("\n🔧 ENVIRONMENT VARIABLES")
        print("=" * 50)
        
        # Load environment variables
        load_dotenv()
        
        # Required environment variables
        required_vars = {
            'DISCORD_BOT_TOKEN': 'Discord bot token for authentication',
            'DATABASE_URL': 'Database connection string',
            'APP_MODE': 'Application mode (development/production)'
        }
        
        # Optional but recommended variables
        optional_vars = {
            'DISCORD_GUILD_ID': 'Discord server ID for faster command sync',
            'LOG_LEVEL': 'Logging level configuration',
            'MAX_CONCURRENT_TASKS': 'Maximum concurrent task limit'
        }
        
        # Check required variables
        missing_required = []
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                display_value = value[:8] + "..." if 'TOKEN' in var else value
                self.log_result(f"Required: {var}", True, f"Set: {display_value}")
            else:
                self.log_result(f"Required: {var}", False, f"Missing - {description}")
                missing_required.append(var)
        
        # Check optional variables
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                self.log_result(f"Optional: {var}", True, f"Set: {value}")
            else:
                self.log_result(f"Optional: {var}", True, f"Not set - {description}")
        
        # Check for old DISCORD_TOKEN (should be removed)
        old_token = os.getenv('DISCORD_TOKEN')
        if old_token:
            self.log_result("Environment Cleanup", False, "Old DISCORD_TOKEN still exists - should use DISCORD_BOT_TOKEN only")
        else:
            self.log_result("Environment Cleanup", True, "No duplicate DISCORD_TOKEN found")
        
        # Overall environment status
        if not missing_required:
            self.log_result("Environment Variables", True, "All required variables present")
        else:
            self.log_result("Environment Variables", False, f"Missing required variables: {', '.join(missing_required)}")
    
    async def verify_database_connection(self) -> None:
        """Verify database connection and basic operations."""
        print("\n💾 DATABASE CONNECTION")
        print("=" * 50)
        
        try:
            database_url = os.getenv('DATABASE_URL', '')
            
            if not database_url:
                self.log_result("Database Configuration", False, "DATABASE_URL not set")
                return
            
            if database_url.startswith('sqlite:///'):
                # SQLite database verification
                db_path = database_url.replace('sqlite:///', '')
                
                # Check if database file exists or can be created
                try:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    
                    # Test connection
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Test basic operations
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                    conn.close()
                    
                    self.log_result("Database Connection", True, f"SQLite database accessible at {db_path}")
                    self.log_result("Database Operations", True, "Basic query operations working")
                    
                except Exception as e:
                    self.log_result("Database Connection", False, f"SQLite connection failed: {e}")
            
            elif database_url.startswith('postgresql://'):
                # PostgreSQL database verification
                try:
                    # Try importing psycopg2
                    import psycopg2
                    from psycopg2 import sql
                    
                    # Test connection
                    conn = psycopg2.connect(database_url)
                    cursor = conn.cursor()
                    
                    # Test basic operations
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                    conn.close()
                    
                    self.log_result("Database Connection", True, "PostgreSQL database accessible")
                    self.log_result("Database Operations", True, "Basic query operations working")
                    
                except ImportError:
                    self.log_result("Database Dependencies", False, "psycopg2 not installed for PostgreSQL")
                except Exception as e:
                    self.log_result("Database Connection", False, f"PostgreSQL connection failed: {e}")
            
            else:
                self.log_result("Database Configuration", False, f"Unsupported database URL format: {database_url}")
                
        except Exception as e:
            self.log_result("Database Verification", False, f"Database verification failed: {e}")
    
    async def verify_agent_integration(self) -> None:
        """Verify that AI agents can be imported and initialized."""
        print("\n🤖 AGENT INTEGRATION")
        print("=" * 50)
        
        # Test agent imports
        agent_imports = {
            'OrchestratorAgent': 'agents.orchestrator_agent',
            'BackendAgent': 'agents.backend_agent', 
            'DatabaseAgent': 'agents.database_agent'
        }
        
        imported_agents = {}
        
        for agent_name, module_path in agent_imports.items():
            try:
                module = __import__(module_path, fromlist=[agent_name])
                agent_class = getattr(module, agent_name)
                imported_agents[agent_name] = agent_class
                self.log_result(f"Import: {agent_name}", True, f"Successfully imported from {module_path}")
            except ImportError as e:
                self.log_result(f"Import: {agent_name}", False, f"Import failed: {e}")
            except AttributeError as e:
                self.log_result(f"Import: {agent_name}", False, f"Class not found: {e}")
            except Exception as e:
                self.log_result(f"Import: {agent_name}", False, f"Unexpected error: {e}")
        
        # Test agent initialization
        initialized_agents = {}
        
        for agent_name, agent_class in imported_agents.items():
            try:
                agent_instance = agent_class(f"Test{agent_name}")
                initialized_agents[agent_name] = agent_instance
                self.log_result(f"Initialize: {agent_name}", True, "Agent instance created successfully")
            except Exception as e:
                self.log_result(f"Initialize: {agent_name}", False, f"Initialization failed: {e}")
        
        # Test basic agent methods
        for agent_name, agent_instance in initialized_agents.items():
            try:
                # Check for essential methods
                essential_methods = ['prepare_for_task']
                available_methods = []
                
                for method_name in essential_methods:
                    if hasattr(agent_instance, method_name):
                        available_methods.append(method_name)
                
                if available_methods:
                    self.log_result(f"Methods: {agent_name}", True, f"Essential methods available: {', '.join(available_methods)}")
                else:
                    self.log_result(f"Methods: {agent_name}", False, "No essential methods found")
                    
            except Exception as e:
                self.log_result(f"Methods: {agent_name}", False, f"Method verification failed: {e}")
        
        # Overall agent integration status
        success_count = len(initialized_agents)
        total_count = len(agent_imports)
        
        if success_count == total_count:
            self.log_result("Agent Integration", True, f"All {total_count} agents successfully integrated")
        else:
            self.log_result("Agent Integration", False, f"Only {success_count}/{total_count} agents working properly")
    
    async def verify_discord_bot_commands(self) -> None:
        """Verify that Discord bot has full command set available."""
        print("\n🤖 DISCORD BOT COMMANDS")
        print("=" * 50)
        
        try:
            # Import the bot
            from bot.main import FullDiscordBot
            
            # Create bot instance
            bot = FullDiscordBot()
            
            self.log_result("Bot Creation", True, "FullDiscordBot instance created successfully")
            
            # Check command tree
            commands = bot.tree.get_commands()
            command_names = [cmd.name for cmd in commands]
            
            self.log_result("Command Tree", True, f"Found {len(commands)} registered commands")
            
            # Expected commands from orchestrator
            expected_commands = [
                'ping',
                'assign-task', 
                'clarify-task',
                'status',
                'approve',
                'pending-prs',
                'emergency-stop'
            ]
            
            # Check each expected command
            missing_commands = []
            for cmd_name in expected_commands:
                if cmd_name in command_names:
                    self.log_result(f"Command: /{cmd_name}", True, "Command registered")
                else:
                    self.log_result(f"Command: /{cmd_name}", False, "Command missing")
                    missing_commands.append(cmd_name)
            
            # Check for extra commands (not necessarily bad)
            extra_commands = [cmd for cmd in command_names if cmd not in expected_commands]
            if extra_commands:
                self.log_result("Extra Commands", True, f"Additional commands found: {', '.join(extra_commands)}")
            
            # Overall command verification
            if not missing_commands:
                self.log_result("Full Command Set", True, f"All {len(expected_commands)} expected commands available")
            else:
                self.log_result("Full Command Set", False, f"Missing commands: {', '.join(missing_commands)}")
                
        except ImportError as e:
            self.log_result("Bot Import", False, f"Could not import FullDiscordBot: {e}")
        except Exception as e:
            self.log_result("Bot Verification", False, f"Bot verification failed: {e}")
    
    async def verify_file_structure(self) -> None:
        """Verify that required files and directories exist."""
        print("\n📁 FILE STRUCTURE")
        print("=" * 50)
        
        # Required files
        required_files = {
            '.env': 'Environment configuration',
            'bot/main.py': 'Main Discord bot implementation',
            'bot/run_bot.py': 'Bot startup script',
            'agents/orchestrator_agent.py': 'Orchestrator agent',
            'agents/backend_agent.py': 'Backend agent',
            'agents/database_agent.py': 'Database agent',
            'agents/orchestrator/commands.py': 'Full command definitions'
        }
        
        # Required directories
        required_dirs = {
            'logs': 'Log files directory',
            'data': 'Data storage directory',
            'agents': 'AI agents directory',
            'bot': 'Discord bot directory'
        }
        
        # Check files
        for file_path, description in required_files.items():
            if os.path.isfile(file_path):
                self.log_result(f"File: {file_path}", True, "Exists")
            else:
                self.log_result(f"File: {file_path}", False, f"Missing - {description}")
        
        # Check directories
        for dir_path, description in required_dirs.items():
            if os.path.isdir(dir_path):
                self.log_result(f"Directory: {dir_path}", True, "Exists")
            else:
                self.log_result(f"Directory: {dir_path}", False, f"Missing - {description}")
        
        # Check .gitignore
        try:
            with open('.gitignore', 'r') as f:
                gitignore_content = f.read()
                
            expected_entries = ['logs/', 'temp/', 'venv/', '__pycache__/', 'data/postgres/']
            found_entries = []
            missing_entries = []
            
            for entry in expected_entries:
                if entry in gitignore_content:
                    found_entries.append(entry)
                else:
                    missing_entries.append(entry)
            
            if not missing_entries:
                self.log_result("Gitignore Configuration", True, f"All expected entries present: {', '.join(found_entries)}")
            else:
                self.log_result("Gitignore Configuration", False, f"Missing entries: {', '.join(missing_entries)}")
                
        except FileNotFoundError:
            self.log_result("Gitignore Configuration", False, ".gitignore file not found")
    
    async def run_all_verifications(self) -> Dict[str, Any]:
        """Run all verification tests."""
        print("🔍 AI AGENT AUTOMATION HUB - SYSTEM VERIFICATION")
        print("=" * 60)
        print("Verifying system restoration and functionality...")
        print()
        
        # Run all verification tests
        await self.verify_environment_variables()
        await self.verify_file_structure()
        await self.verify_database_connection()
        await self.verify_agent_integration()
        await self.verify_discord_bot_commands()
        
        # Generate summary
        print("\n📊 VERIFICATION SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests Run: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print()
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED - System is fully restored and functional!")
            print("\nYou can now:")
            print("  • Start the bot with: python bot/run_bot.py")
            print("  • Use all Discord commands: /assign-task, /status, /approve, etc.")
            print("  • Deploy to production with confidence")
        else:
            print("⚠️  SOME TESTS FAILED - System needs attention")
            print("\nIssues found:")
            for issue in self.issues:
                print(f"  • {issue}")
            print("\nPlease fix these issues before proceeding.")
        
        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            'issues': self.issues,
            'results': self.results
        }


async def main():
    """Main verification function."""
    try:
        verifier = SystemVerifier()
        summary = await verifier.run_all_verifications()
        
        # Return appropriate exit code
        if summary['failed'] == 0:
            return 0  # Success
        else:
            return 1  # Failure
            
    except Exception as e:
        print(f"\n💥 VERIFICATION CRASHED: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return 2  # Critical failure


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Verification cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        sys.exit(2)