#!/usr/bin/env python3
"""
Testing Agent Main Entry Point

Starts the testing agent that monitors PRs and runs automated tests.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from aiohttp import web
import threading

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.testing.testing_agent import TestingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/testing_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global testing agent instance for health checks
testing_agent_instance = None

async def health_check(request):
    """Health check endpoint for Docker monitoring."""
    try:
        if testing_agent_instance is None:
            return web.json_response(
                {"status": "unhealthy", "reason": "Testing agent not initialized"}, 
                status=503
            )
        
        status = await testing_agent_instance.get_status()
        
        return web.json_response({
            "status": "healthy",
            "agent": "testing-agent",
            "online": True,
            "active_tests": status.get("active_tests", 0),
            "auto_approve": status.get("auto_approve", False),
            "workspace": str(status.get("workspace", "unknown")),
            "uptime": "running"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response(
            {"status": "unhealthy", "reason": str(e)}, 
            status=503
        )

async def status_endpoint(request):
    """Detailed status endpoint."""
    try:
        if testing_agent_instance is None:
            return web.json_response(
                {"error": "Testing agent not initialized"}, 
                status=503
            )
        
        status = await testing_agent_instance.get_status()
        return web.json_response(status)
    except Exception as e:
        logger.error(f"Status endpoint failed: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def start_web_server():
    """Start health check web server."""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status_endpoint)
    app.router.add_get('/', health_check)  # Root endpoint also serves health
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8083)
    await site.start()
    logger.info("Health check server started on port 8083")

async def main():
    """Main entry point for the testing agent."""
    global testing_agent_instance
    
    try:
        logger.info("Starting Testing Agent...")
        
        # Start health check server
        await start_web_server()
        
        # Initialize testing agent
        testing_agent_instance = TestingAgent()
        
        # Start monitoring PRs (this will run indefinitely)
        await testing_agent_instance.start()
        
    except KeyboardInterrupt:
        logger.info("Testing Agent stopped by user")
    except Exception as e:
        logger.error(f"Testing Agent failed to start: {e}")
        raise
    finally:
        testing_agent_instance = None

if __name__ == "__main__":
    asyncio.run(main())