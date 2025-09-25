import asyncio
import logging
from agents.backend.backend_agent import BackendAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Backend Agent...")
    agent = BackendAgent()
    await agent.initialize()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())