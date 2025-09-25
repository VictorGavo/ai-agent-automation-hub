#!/usr/bin/env python3
"""
Example script demonstrating the Discord approval workflow commands.

This script shows how to use the new Discord commands for PR approval:
- /approve [pr-number] - Approve and merge a specific PR
- /review [pr-number] - Show PR details for review
- /reject [pr-number] [reason] - Reject a PR with reason
- /status - Enhanced status with PR info
- /pending-prs - Show all open PRs awaiting approval

Prerequisites:
1. Discord bot is running with the orchestrator
2. GitHub client is properly configured
3. Bot has necessary permissions in Discord server
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.orchestrator.orchestrator import OrchestratorAgent
from agents.backend.github_client import GitHubClient

async def test_discord_approval_workflow():
    """Test the Discord approval workflow functionality"""
    print("🤖 Testing Discord Approval Workflow")
    print("=" * 50)
    
    # Initialize components
    orchestrator = OrchestratorAgent()
    await orchestrator.initialize()
    
    # Test 1: Check GitHub client availability
    print("\n1. Testing GitHub Client Connection...")
    if orchestrator.github_client:
        stats = orchestrator.github_client.get_stats()
        print(f"✅ GitHub client connected to: {stats.get('repository')}")
        print(f"   Default branch: {stats.get('default_branch')}")
    else:
        print("❌ GitHub client not available")
        return
    
    # Test 2: List pending PRs
    print("\n2. Testing Pending PRs List...")
    try:
        pending_result = await orchestrator.list_pending_prs(5)
        if pending_result["success"]:
            prs = pending_result["prs"]
            print(f"✅ Found {len(prs)} open PRs")
            for pr in prs[:3]:  # Show first 3
                print(f"   #{pr['number']}: {pr['title'][:50]}...")
        else:
            print(f"❌ Failed to list PRs: {pending_result['message']}")
    except Exception as e:
        print(f"❌ Error listing PRs: {e}")
    
    # Test 3: Get PR details (if we have PRs)
    print("\n3. Testing PR Details Retrieval...")
    try:
        pending_result = await orchestrator.list_pending_prs(1)
        if pending_result["success"] and pending_result["prs"]:
            pr_number = pending_result["prs"][0]["number"]
            pr_details = await orchestrator.github_client.get_pull_request(pr_number)
            if pr_details:
                print(f"✅ Successfully retrieved details for PR #{pr_number}")
                print(f"   Title: {pr_details['title']}")
                print(f"   Author: {pr_details['author']}")
                print(f"   Files changed: {pr_details['files_changed_count']}")
                print(f"   Mergeable: {pr_details['mergeable']}")
            else:
                print(f"❌ Failed to get details for PR #{pr_number}")
        else:
            print("ℹ️  No open PRs to test details retrieval")
    except Exception as e:
        print(f"❌ Error getting PR details: {e}")
    
    # Test 4: Status report with PR info
    print("\n4. Testing Enhanced Status Report...")
    try:
        status = await orchestrator.get_status_report()
        if "error" not in status:
            print("✅ Status report generated successfully")
            print(f"   System status: {status.get('orchestrator_status', 'unknown')}")
            
            tasks = status.get('tasks', {})
            print(f"   Tasks - Total: {tasks.get('total', 0)}, Pending: {tasks.get('pending', 0)}")
            
            prs = status.get('prs', {})
            print(f"   PRs - Open: {prs.get('open_prs', 'N/A')}, Awaiting: {prs.get('awaiting_approval', 0)}")
        else:
            print(f"❌ Status report error: {status['error']}")
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Discord Approval Workflow Test Complete!")
    print("\nNew Discord Commands Available:")
    print("• /approve [pr-number] - Approve and merge PR")
    print("• /review [pr-number] - Interactive PR review")
    print("• /reject [pr-number] [reason] - Reject PR with reason")
    print("• /pending-prs [limit] - List open PRs")
    print("• /status - Enhanced status with PR metrics")
    print("\nMobile-Friendly Features:")
    print("• Interactive approve/reject buttons")
    print("• Detailed PR summaries")
    print("• Real-time status updates")
    print("• Quick action shortcuts")

def print_usage_examples():
    """Print usage examples for the new Discord commands"""
    print("\n🔧 Discord Command Usage Examples:")
    print("=" * 50)
    
    examples = [
        {
            "command": "/status",
            "description": "Get comprehensive system status including PR metrics",
            "example": "/status"
        },
        {
            "command": "/pending-prs",
            "description": "List all open PRs awaiting approval",
            "example": "/pending-prs 10"
        },
        {
            "command": "/review",
            "description": "Show detailed PR info with approve/reject buttons",
            "example": "/review 42"
        },
        {
            "command": "/approve",
            "description": "Quickly approve and merge a PR",
            "example": "/approve 42"
        },
        {
            "command": "/reject",
            "description": "Reject a PR with a specific reason",
            "example": "/reject 42 \"Needs more tests before merging\""
        }
    ]
    
    for cmd in examples:
        print(f"\n📱 {cmd['command']}")
        print(f"   {cmd['description']}")
        print(f"   Usage: {cmd['example']}")
    
    print("\n🎯 Mobile Workflow:")
    print("1. Get notification of new PR")
    print("2. Use /review [pr-number] to see details")
    print("3. Tap ✅ Approve or ❌ Reject buttons")
    print("4. For rejection, enter reason in popup")
    print("5. Get confirmation and task updates")

async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        print_usage_examples()
        return
    
    # Check environment
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN environment variable not set")
        print("   Please set your GitHub token to test the workflow")
        return
    
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable not set")
        print("   Please configure your database to test the workflow")
        return
    
    try:
        await test_discord_approval_workflow()
        print_usage_examples()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Discord Approval Workflow Test")
    print("Usage: python discord_approval_workflow.py [--examples]")
    print("=" * 60)
    
    asyncio.run(main())