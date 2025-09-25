#!/usr/bin/env python3
"""
Testing Agent Status Checker

Quick status check tool to see if the Testing Agent is running and healthy.
"""

import asyncio
import aiohttp
import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path

async def check_docker_status():
    """Check if testing agent Docker container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=automation_hub_testing_agent", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Header + at least one container
                container_line = lines[1]
                if "Up" in container_line:
                    return {"running": True, "status": container_line}
                else:
                    return {"running": False, "status": container_line}
            else:
                return {"running": False, "status": "Container not found"}
        else:
            return {"running": False, "status": f"Docker error: {result.stderr}"}
    except Exception as e:
        return {"running": False, "status": f"Error checking Docker: {e}"}

async def check_health_endpoint():
    """Check the testing agent health endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8083/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"healthy": True, "data": data}
                else:
                    return {"healthy": False, "status": response.status, "data": None}
    except asyncio.TimeoutError:
        return {"healthy": False, "status": "timeout", "data": None}
    except Exception as e:
        return {"healthy": False, "status": str(e), "data": None}

async def check_detailed_status():
    """Get detailed status from the agent."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8083/status", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                else:
                    return {"success": False, "status": response.status}
    except Exception as e:
        return {"success": False, "error": str(e)}

def print_status_report(docker_status, health_status, detailed_status):
    """Print a comprehensive status report."""
    print("🧪 Testing Agent Status Report")
    print("=" * 50)
    print(f"Checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Docker Status
    print("🐳 Docker Container:")
    if docker_status["running"]:
        print(f"   ✅ Running - {docker_status['status']}")
    else:
        print(f"   ❌ Not Running - {docker_status['status']}")
    print()
    
    # Health Check
    print("💚 Health Check (http://localhost:8083/health):")
    if health_status["healthy"]:
        print(f"   ✅ Healthy")
        if health_status["data"]:
            data = health_status["data"]
            print(f"   📊 Active Tests: {data.get('active_tests', 'N/A')}")
            print(f"   🤖 Auto-Approve: {data.get('auto_approve', 'N/A')}")
            print(f"   📁 Workspace: {data.get('workspace', 'N/A')}")
    else:
        print(f"   ❌ Unhealthy - {health_status['status']}")
    print()
    
    # Detailed Status
    print("📊 Detailed Status:")
    if detailed_status["success"]:
        data = detailed_status["data"]
        print(f"   ✅ Agent: {data.get('agent', 'testing-agent')}")
        print(f"   🔄 Status: {data.get('status', 'unknown')}")
        print(f"   🧪 Active Tests: {data.get('active_tests', 0)}")
        print(f"   📈 Tested Commits: {data.get('tested_commits', 0)}")
        print(f"   🤖 Auto-Approve: {data.get('auto_approve', False)}")
        print(f"   ⏱️ Polling Interval: {data.get('polling_interval', 'N/A')}s")
        print(f"   📁 Workspace: {data.get('workspace', 'N/A')}")
    else:
        error = detailed_status.get('error', detailed_status.get('status', 'Unknown error'))
        print(f"   ❌ Failed to get status - {error}")
    print()
    
    # Overall Status
    overall_healthy = (
        docker_status["running"] and 
        health_status["healthy"] and 
        detailed_status["success"]
    )
    
    print("🎯 Overall Status:")
    if overall_healthy:
        print("   ✅ Testing Agent is RUNNING and HEALTHY")
        print("   🚀 Ready to test PRs automatically!")
        print()
        print("💡 Quick Commands:")
        print("   /test-status    - Check from Discord")
        print("   /test-pr 42     - Test specific PR")
        print("   /test-config    - Adjust settings")
    else:
        print("   ❌ Testing Agent has ISSUES")
        print()
        print("🔧 Troubleshooting:")
        if not docker_status["running"]:
            print("   • Start with: docker-compose up testing-agent")
        if not health_status["healthy"]:
            print("   • Check logs: docker-compose logs testing-agent")
        if not detailed_status["success"]:
            print("   • Verify ports: netstat -tlnp | grep 8083")
    print()

async def main():
    """Main status check function."""
    print("Checking Testing Agent status...")
    print()
    
    # Run all checks concurrently
    docker_status, health_status, detailed_status = await asyncio.gather(
        check_docker_status(),
        check_health_endpoint(),
        check_detailed_status()
    )
    
    print_status_report(docker_status, health_status, detailed_status)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Status check cancelled")
    except Exception as e:
        print(f"\n💥 Status check failed: {e}")
        sys.exit(1)