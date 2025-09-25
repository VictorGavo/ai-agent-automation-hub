#!/bin/bash
"""
Reliability System Startup Script

Starts the AI Agent Automation Hub with full reliability features enabled.
This script ensures all reliability components are properly initialized.
"""

import os
import sys
import subprocess
import logging
import signal
import time
from typing import Optional
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from safety_monitor import get_safety_monitor
from utils.task_state_manager import get_task_state_manager
from utils.safe_git_operations import get_safe_git_operations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reliability_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ReliabilitySystemManager:
    """Manages the startup and shutdown of the reliability system."""
    
    def __init__(self):
        self.safety_monitor = None
        self.task_state_manager = None
        self.safe_git = None
        self.discord_bot_process = None
        self.running = False
    
    def initialize_components(self) -> bool:
        """Initialize all reliability components."""
        try:
            logger.info("🚀 Starting AI Agent Automation Hub Reliability System")
            logger.info("=" * 60)
            
            # Ensure required directories exist
            os.makedirs('logs', exist_ok=True)
            os.makedirs('data', exist_ok=True)
            
            # Initialize task state manager
            logger.info("📋 Initializing Task State Manager...")
            self.task_state_manager = get_task_state_manager()
            logger.info("✅ Task State Manager initialized")
            
            # Initialize safe git operations
            logger.info("🌿 Initializing Safe Git Operations...")
            try:
                self.safe_git = get_safe_git_operations()
                git_status = self.safe_git.get_safety_status()
                
                if git_status.get('recommendations'):
                    logger.warning("Git safety recommendations:")
                    for rec in git_status['recommendations']:
                        logger.warning(f"  - {rec}")
                
                logger.info("✅ Safe Git Operations initialized")
            except Exception as e:
                logger.error(f"❌ Git initialization failed: {e}")
                return False
            
            # Initialize safety monitor
            logger.info("🛡️ Initializing Safety Monitor...")
            config = {
                'monitoring_interval': 30,
                'alert_cooldown': 300,
                'db_path': 'data/safety_monitor.db'
            }
            
            self.safety_monitor = get_safety_monitor(config)
            self.safety_monitor.start_monitoring()
            logger.info("✅ Safety Monitor started")
            
            # Verify system health
            logger.info("🏥 Checking system health...")
            health = self.safety_monitor.get_system_health()
            
            if health.get('is_overloaded'):
                logger.warning("⚠️ System appears overloaded - consider safe mode")
                for warning in health.get('warnings', []):
                    logger.warning(f"  - {warning}")
            else:
                logger.info("✅ System health looks good")
            
            logger.info("=" * 60)
            logger.info("🎉 Reliability System initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize reliability system: {e}")
            return False
    
    def start_discord_bot(self) -> bool:
        """Start the Discord bot with reliability features."""
        try:
            logger.info("🤖 Starting Discord Bot...")
            
            # Check if Discord token is available
            if not os.getenv('DISCORD_BOT_TOKEN'):
                logger.error("❌ DISCORD_BOT_TOKEN environment variable not set")
                return False
            
            # Start Discord bot as subprocess
            bot_script = Path(__file__).parent / 'bot' / 'main.py'
            
            self.discord_bot_process = subprocess.Popen([
                sys.executable, str(bot_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if process is still running
            if self.discord_bot_process.poll() is None:
                logger.info("✅ Discord Bot started successfully")
                return True
            else:
                logger.error("❌ Discord Bot failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start Discord bot: {e}")
            return False
    
    def run(self) -> None:
        """Run the complete reliability system."""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialize components
            if not self.initialize_components():
                logger.error("❌ Component initialization failed")
                return
            
            # Start Discord bot
            if not self.start_discord_bot():
                logger.error("❌ Discord bot startup failed")
                return
            
            self.running = True
            logger.info("🚀 Reliability System is now running")
            logger.info("   Discord bot commands available:")
            logger.info("   - /system-health - Check system status")
            logger.info("   - /safe-mode - Control agent operations")
            logger.info("   - /rollback - Recovery options")
            logger.info("   - /resume-task - Resume interrupted tasks")
            logger.info("   - /assign-task - Create new tasks with reliability")
            logger.info("")
            logger.info("💡 Press Ctrl+C to shutdown gracefully")
            
            # Main loop - monitor the Discord bot process
            while self.running:
                time.sleep(10)
                
                # Check Discord bot health
                if self.discord_bot_process and self.discord_bot_process.poll() is not None:
                    logger.error("❌ Discord bot process died, attempting restart...")
                    if not self.start_discord_bot():
                        logger.error("❌ Failed to restart Discord bot")
                        break
                
                # Monitor system health
                if self.safety_monitor:
                    health = self.safety_monitor.get_system_health()
                    if health.get('is_overloaded') and not health.get('safe_mode_active'):
                        logger.warning("⚠️ System overload detected - activating safe mode")
                        self.safety_monitor.activate_safe_mode("System overload - automatic activation")
        
        except KeyboardInterrupt:
            logger.info("⏹️ Shutdown requested by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Gracefully shutdown all components."""
        logger.info("🛑 Shutting down Reliability System...")
        self.running = False
        
        # Stop Discord bot
        if self.discord_bot_process:
            logger.info("🤖 Stopping Discord bot...")
            self.discord_bot_process.terminate()
            try:
                self.discord_bot_process.wait(timeout=10)
                logger.info("✅ Discord bot stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Discord bot didn't stop gracefully, forcing...")
                self.discord_bot_process.kill()
        
        # Stop safety monitor
        if self.safety_monitor:
            logger.info("🛡️ Stopping safety monitor...")
            self.safety_monitor.stop_monitoring()
            logger.info("✅ Safety monitor stopped")
        
        logger.info("✅ Reliability System shutdown complete")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"📡 Received signal {signum}")
        self.running = False


def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    logger.info("🔍 Checking prerequisites...")
    
    checks = []
    
    # Check if in git repository
    try:
        subprocess.run(['git', 'status'], check=True, capture_output=True)
        checks.append(("Git repository", True, "✅"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks.append(("Git repository", False, "❌ Not in a git repository"))
    
    # Check environment variables
    discord_token = bool(os.getenv('DISCORD_BOT_TOKEN'))
    checks.append(("Discord token", discord_token, "✅" if discord_token else "❌ DISCORD_BOT_TOKEN not set"))
    
    # Check Python packages
    try:
        import discord
        import psutil
        import sqlite3
        checks.append(("Required packages", True, "✅"))
    except ImportError as e:
        checks.append(("Required packages", False, f"❌ Missing package: {e}"))
    
    # Check write permissions
    try:
        test_file = 'data/test_write.tmp'
        os.makedirs('data', exist_ok=True)
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        checks.append(("Write permissions", True, "✅"))
    except Exception as e:
        checks.append(("Write permissions", False, f"❌ Cannot write to data directory: {e}"))
    
    # Print results
    all_passed = True
    for check_name, passed, message in checks:
        logger.info(f"  {message} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Main entry point."""
    print("🤖 AI Agent Automation Hub - Reliability System")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed")
        print("\n💡 Setup instructions:")
        print("  1. Ensure you're in a git repository")
        print("  2. Set DISCORD_BOT_TOKEN environment variable")
        print("  3. Install required packages: pip install -r requirements.txt")
        print("  4. Ensure write permissions to data/ directory")
        return 1
    
    # Create and run the reliability system manager
    manager = ReliabilitySystemManager()
    manager.run()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())