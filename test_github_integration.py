#!/usr/bin/env python3
"""
GitHub Integration Test Script

Comprehensive test of GitHub integration functionality in the AI Agent Automation Hub.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from agents.orchestrator_agent import OrchestratorAgent
from bot.main import FullDiscordBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_github_integration():
    """Test GitHub integration comprehensively."""
    
    print("🔍 AI AGENT AUTOMATION HUB - GITHUB INTEGRATION TEST")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    results = {}
    
    # Test 1: Environment Configuration
    print("\n🔧 TESTING ENVIRONMENT CONFIGURATION")
    print("-" * 40)
    
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPO', 'VictorGavo/ai-agent-automation-hub')
    
    if github_token:
        print(f"✅ GitHub Token: Present ({github_token[:12]}...)")
        results['token'] = True
    else:
        print("❌ GitHub Token: Missing")
        results['token'] = False
    
    print(f"✅ GitHub Repository: {github_repo}")
    results['repo_config'] = True
    
    # Test 2: Orchestrator Agent GitHub Integration
    print("\n🤖 TESTING ORCHESTRATOR AGENT")
    print("-" * 40)
    
    try:
        orchestrator = OrchestratorAgent("GitHubTestOrchestrator")
        print("✅ Orchestrator Agent: Created")
        
        # Initialize GitHub client
        github_success = await orchestrator.initialize_github_client()
        if github_success:
            print("✅ GitHub Client: Initialized")
            results['orchestrator_github'] = True
            
            # Test GitHub stats
            stats = orchestrator.github_client.get_stats()
            print(f"✅ Repository Access: {stats['repository']}")
            print(f"✅ Default Branch: {stats['default_branch']}")
            print(f"✅ Connection Status: {'Connected' if stats['client_initialized'] else 'Disconnected'}")
            results['repo_access'] = stats['client_initialized']
            
        else:
            print("❌ GitHub Client: Initialization Failed")
            results['orchestrator_github'] = False
            results['repo_access'] = False
            
    except Exception as e:
        print(f"❌ Orchestrator Agent: Failed - {e}")
        results['orchestrator_github'] = False
        results['repo_access'] = False
    
    # Test 3: GitHub Operations
    print("\n🔄 TESTING GITHUB OPERATIONS")
    print("-" * 40)
    
    if results.get('orchestrator_github'):
        try:
            # Test PR listing
            pr_result = await orchestrator.list_pending_prs(5)
            if pr_result['success']:
                prs = pr_result['prs']
                print(f"✅ PR Listing: Found {len(prs)} open PRs")
                results['pr_listing'] = True
                
                if prs:
                    print("   Open PRs:")
                    for pr in prs[:3]:
                        print(f"     - #{pr['number']}: {pr['title'][:50]}")
                        print(f"       Author: {pr['author']}, Mergeable: {pr['mergeable']}")
                else:
                    print("   No open PRs found")
            else:
                print(f"❌ PR Listing: Failed - {pr_result['message']}")
                results['pr_listing'] = False
                
            # Test status report
            status = await orchestrator.get_status_report()
            if 'error' not in status:
                print("✅ Status Report: Generated")
                print(f"   Orchestrator Status: {status['orchestrator_status']}")
                print(f"   Active Tasks: {status['tasks']['total']}")
                results['status_report'] = True
            else:
                print(f"❌ Status Report: Failed - {status['error']}")
                results['status_report'] = False
                
        except Exception as e:
            print(f"❌ GitHub Operations: Failed - {e}")
            results['pr_listing'] = False
            results['status_report'] = False
    else:
        print("⚠️  Skipping GitHub operations (client not initialized)")
        results['pr_listing'] = False
        results['status_report'] = False
    
    # Test 4: Discord Bot Integration
    print("\n🤖 TESTING DISCORD BOT INTEGRATION")
    print("-" * 40)
    
    try:
        bot = FullDiscordBot()
        print("✅ Discord Bot: Created")
        
        # Check commands
        commands = bot.tree.get_commands()
        expected_commands = ['ping', 'assign-task', 'clarify-task', 'status', 'approve', 'pending-prs', 'emergency-stop']
        
        found_commands = [cmd.name for cmd in commands]
        missing_commands = [cmd for cmd in expected_commands if cmd not in found_commands]
        
        if not missing_commands:
            print(f"✅ Commands: All {len(expected_commands)} commands registered")
            results['discord_commands'] = True
        else:
            print(f"❌ Commands: Missing {missing_commands}")
            results['discord_commands'] = False
        
        # Test bot with orchestrator
        if results.get('orchestrator_github'):
            bot.orchestrator = orchestrator
            print("✅ Bot-Orchestrator Integration: Connected")
            results['bot_orchestrator'] = True
        else:
            print("⚠️  Bot-Orchestrator Integration: Limited (no GitHub)")
            results['bot_orchestrator'] = False
            
    except Exception as e:
        print(f"❌ Discord Bot: Failed - {e}")
        results['discord_commands'] = False
        results['bot_orchestrator'] = False
    
    # Test 5: Full Workflow Test
    print("\n🚀 TESTING FULL WORKFLOW")
    print("-" * 40)
    
    if results.get('orchestrator_github') and results.get('discord_commands'):
        try:
            # Test assign task
            task_result = await orchestrator.assign_task(
                description="Test GitHub integration functionality",
                user_id="test_user_123",
                channel_id="test_channel_456",
                priority="medium"
            )
            
            if task_result['success']:
                print("✅ Task Assignment: Working")
                print(f"   Task ID: {task_result['task_id']}")
                results['task_assignment'] = True
            else:
                print(f"❌ Task Assignment: Failed - {task_result.get('message')}")
                results['task_assignment'] = False
                
        except Exception as e:
            print(f"❌ Full Workflow: Failed - {e}")
            results['task_assignment'] = False
    else:
        print("⚠️  Skipping full workflow test (dependencies not met)")
        results['task_assignment'] = False
    
    # Generate Summary
    print("\n📊 GITHUB INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print("\nTest Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("GitHub integration is fully functional and ready for use!")
        print("\nYou can now use Discord commands:")
        print("  • /pending-prs - List open pull requests")
        print("  • /approve [pr-number] - Approve and merge PRs")
        print("  • /status - View system status with GitHub integration")
        print("  • /assign-task - Create tasks that can generate PRs")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Check the failed tests above and ensure:")
        print("  • GitHub token is valid and has repository access")
        print("  • Repository exists and is accessible")
        print("  • All dependencies are properly installed")
    
    return success_rate == 100.0


async def main():
    """Main test function."""
    try:
        success = await test_github_integration()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 TEST CRASH: {e}")
        import traceback
        print(traceback.format_exc())
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    print(f"\nExiting with code: {exit_code}")
    sys.exit(exit_code)