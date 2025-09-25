#!/usr/bin/env python3
"""
Testing Agent Monitor

Real-time monitoring tool to watch Testing Agent activity.
Shows live status updates, test progress, and notifications.
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)

class TestingAgentMonitor:
    """Real-time monitor for Testing Agent activities."""
    
    def __init__(self, agent_url="http://localhost:8083"):
        self.agent_url = agent_url
        self.last_status = {}
        self.session = None
    
    async def start_monitoring(self):
        """Start real-time monitoring."""
        print("🧪 Testing Agent Monitor Started")
        print("=" * 60)
        print(f"Monitoring: {self.agent_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.session = aiohttp.ClientSession()
        
        try:
            while True:
                await self._check_status()
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
        finally:
            if self.session:
                await self.session.close()
    
    async def _check_status(self):
        """Check agent status and show changes."""
        try:
            async with self.session.get(f"{self.agent_url}/status", timeout=5) as response:
                if response.status == 200:
                    current_status = await response.json()
                    self._display_status_changes(current_status)
                    self.last_status = current_status
                else:
                    self._display_error(f"HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            self._display_error("Connection timeout")
        except Exception as e:
            self._display_error(f"Connection failed: {e}")
    
    def _display_status_changes(self, current_status):
        """Display status changes and current state."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Check for status changes
        if not self.last_status:
            # First status check
            print(f"[{timestamp}] 🟢 Testing Agent Online")
            print(f"[{timestamp}] 📊 Status: {self._format_status(current_status)}")
            return
        
        # Check for active test changes
        current_tests = current_status.get('active_tests', 0)
        last_tests = self.last_status.get('active_tests', 0)
        
        if current_tests != last_tests:
            if current_tests > last_tests:
                print(f"[{timestamp}] 🧪 New test started (Total: {current_tests})")
            else:
                print(f"[{timestamp}] ✅ Test completed (Remaining: {current_tests})")
        
        # Check for configuration changes
        if current_status.get('auto_approve') != self.last_status.get('auto_approve'):
            auto_approve = "Enabled" if current_status.get('auto_approve') else "Disabled"
            print(f"[{timestamp}] ⚙️ Auto-approve: {auto_approve}")
        
        # Show periodic status (every minute)
        if int(timestamp.split(':')[2]) % 60 == 0:  # Every minute
            print(f"[{timestamp}] 📊 Status: {self._format_status(current_status)}")
    
    def _format_status(self, status):
        """Format status for display."""
        active_tests = status.get('active_tests', 0)
        auto_approve = "On" if status.get('auto_approve', False) else "Off"
        
        parts = [
            f"Tests: {active_tests}",
            f"Auto-approve: {auto_approve}"
        ]
        
        return " | ".join(parts)
    
    def _display_error(self, error):
        """Display connection error."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] ❌ {error}")

def print_usage():
    """Print usage instructions."""
    print("""
🧪 Testing Agent Monitor Usage

This tool provides real-time monitoring of Testing Agent activities.

Commands:
  python scripts/monitor_testing_agent.py          # Monitor localhost
  python scripts/monitor_testing_agent.py --help  # Show this help

What you'll see:
  🟢 Agent online/offline status
  🧪 When tests start and complete  
  ⚙️ Configuration changes
  📊 Periodic status summaries
  ❌ Connection errors

Press Ctrl+C to stop monitoring.

Make sure the Testing Agent is running:
  docker-compose up testing-agent
""")

async def main():
    """Main monitoring function."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print_usage()
        return
    
    # Determine agent URL
    agent_url = "http://localhost:8083"
    if len(sys.argv) > 1:
        agent_url = sys.argv[1]
    
    monitor = TestingAgentMonitor(agent_url)
    await monitor.start_monitoring()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Monitor failed: {e}")
        sys.exit(1)