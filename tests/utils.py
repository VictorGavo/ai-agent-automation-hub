"""
Test utilities and mock objects for the AI Agent Automation Hub tests.
"""

import asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock
import uuid
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class TestConfig:
    """Test configuration class."""
    database_url: str = "postgresql://test:test@localhost/test_db"
    discord_token: str = "test_token_12345"
    max_concurrent_tasks: int = 2
    log_level: str = "DEBUG"
    app_mode: str = "testing"

class MockDatabase:
    """Mock database for testing."""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.logs: List[Dict] = []
        self.agents: Dict[str, Dict] = {}
        self.connected = False
    
    async def setup(self):
        """Setup the mock database."""
        self.connected = True
        await self.create_default_data()
    
    async def cleanup(self):
        """Cleanup the mock database."""
        self.tasks.clear()
        self.logs.clear()
        self.agents.clear()
        self.connected = False
    
    async def create_default_data(self):
        """Create some default test data."""
        # Create test agents
        self.agents = {
            'backend': {
                'id': 'backend',
                'name': 'Backend Agent',
                'status': 'healthy',
                'last_heartbeat': datetime.now()
            },
            'testing': {
                'id': 'testing',
                'name': 'Testing Agent', 
                'status': 'healthy',
                'last_heartbeat': datetime.now()
            },
            'orchestrator': {
                'id': 'orchestrator',
                'name': 'Orchestrator',
                'status': 'healthy', 
                'last_heartbeat': datetime.now()
            }
        }
    
    async def create_task(self, task_data: Dict) -> str:
        """Create a new task."""
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {
            'id': task_id,
            'title': task_data.get('title', 'Test Task'),
            'description': task_data.get('description', 'Test Description'),
            'agent_type': task_data.get('agent_type', 'backend'),
            'status': 'pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'result': None,
            'error': None
        }
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    async def update_task(self, task_id: str, updates: Dict) -> bool:
        """Update a task."""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].update(updates)
        self.tasks[task_id]['updated_at'] = datetime.now()
        return True
    
    async def list_tasks(self, filters: Optional[Dict] = None) -> List[Dict]:
        """List tasks with optional filters."""
        tasks = list(self.tasks.values())
        
        if filters:
            if 'status' in filters:
                tasks = [t for t in tasks if t['status'] == filters['status']]
            if 'agent_type' in filters:
                tasks = [t for t in tasks if t['agent_type'] == filters['agent_type']]
        
        return tasks
    
    async def log_event(self, event_data: Dict):
        """Log an event."""
        self.logs.append({
            'id': len(self.logs) + 1,
            'timestamp': datetime.now(),
            **event_data
        })
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get agent status."""
        return self.agents.get(agent_id)

class MockDiscordBot:
    """Mock Discord bot for testing."""
    
    def __init__(self):
        self.user = Mock()
        self.user.id = 123456789
        self.user.name = "TestBot"
        self.user.discriminator = "0001"
        
        self.guilds = []
        self.sent_messages = []
        self.interactions = []
        
        # Mock methods
        self.wait_for = AsyncMock()
        self.get_channel = Mock()
        self.get_guild = Mock()
        self.get_user = Mock()
    
    async def send_message(self, channel_id: int, content: str = None, embed=None, view=None):
        """Mock sending a message."""
        message = {
            'channel_id': channel_id,
            'content': content,
            'embed': embed,
            'view': view,
            'timestamp': datetime.now()
        }
        self.sent_messages.append(message)
        return Mock(id=len(self.sent_messages))
    
    async def edit_message(self, message_id: int, content: str = None, embed=None, view=None):
        """Mock editing a message."""
        # Find and update the message
        for msg in self.sent_messages:
            if hasattr(msg, 'id') and msg.id == message_id:
                if content:
                    msg['content'] = content
                if embed:
                    msg['embed'] = embed
                if view:
                    msg['view'] = view
                return True
        return False
    
    def add_cog(self, cog):
        """Mock adding a cog."""
        pass
    
    async def sync(self, guild=None):
        """Mock syncing slash commands."""
        pass

class MockInteraction:
    """Mock Discord interaction for testing."""
    
    def __init__(self, user_id: int = 123456789, guild_id: int = 987654321):
        self.user = Mock()
        self.user.id = user_id
        self.user.name = "TestUser"
        self.user.display_name = "Test User"
        
        self.guild = Mock() if guild_id else None
        if self.guild:
            self.guild.id = guild_id
        
        self.channel = Mock()
        self.channel.id = 555555555
        
        self.response = Mock()
        self.response.send_message = AsyncMock()
        self.response.edit_message = AsyncMock()
        self.response.defer = AsyncMock()
        
        self.followup = Mock()
        self.followup.send = AsyncMock()
        
        self.data = {}
        self.responded = False
    
    async def response_send_message(self, content: str = None, embed=None, view=None, ephemeral: bool = False):
        """Mock responding to interaction."""
        self.responded = True
        return await self.response.send_message(
            content=content, 
            embed=embed, 
            view=view, 
            ephemeral=ephemeral
        )

class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, agent_type: str = "backend"):
        self.agent_type = agent_type
        self.status = "healthy"
        self.tasks_processed = 0
        self.last_heartbeat = datetime.now()
        
        # Mock methods with default behaviors
        self.process_task = AsyncMock()
        self.get_status = Mock(return_value=self.status)
        self.health_check = AsyncMock(return_value=True)
    
    async def mock_process_task(self, task_data: Dict) -> Dict:
        """Mock processing a task."""
        await asyncio.sleep(0.1)  # Simulate processing time
        self.tasks_processed += 1
        
        return {
            'success': True,
            'result': f'Mock {self.agent_type} agent processed task successfully',
            'metadata': {
                'agent_type': self.agent_type,
                'processing_time': 0.1,
                'tasks_processed': self.tasks_processed
            }
        }

class MockTaskManager:
    """Mock task manager for testing."""
    
    def __init__(self, db: MockDatabase):
        self.db = db
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Dict] = {}
    
    async def create_task(self, task_data: Dict) -> str:
        """Create a new task."""
        task_id = await self.db.create_task(task_data)
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a task."""
        return await self.db.get_task(task_id)
    
    async def execute_task(self, task_id: str, agent: MockAgent) -> Dict:
        """Execute a task with an agent."""
        task = await self.get_task(task_id)
        if not task:
            return {'success': False, 'error': 'Task not found'}
        
        # Update task status
        await self.db.update_task(task_id, {'status': 'running'})
        
        try:
            # Process with agent
            result = await agent.mock_process_task(task)
            
            # Update task with result
            await self.db.update_task(task_id, {
                'status': 'completed',
                'result': result['result']
            })
            
            self.task_results[task_id] = result
            return result
            
        except Exception as e:
            await self.db.update_task(task_id, {
                'status': 'failed',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}

def create_test_task(
    title: str = "Test Task",
    description: str = "Test task description", 
    agent_type: str = "backend"
) -> Dict:
    """Create a test task dictionary."""
    return {
        'title': title,
        'description': description,
        'agent_type': agent_type,
        'priority': 'medium',
        'metadata': {}
    }

def assert_task_created(task_id: str, db: MockDatabase):
    """Assert that a task was created successfully."""
    assert task_id is not None
    assert len(task_id) == 8  # UUID prefix length
    assert task_id in db.tasks

def assert_message_sent(bot: MockDiscordBot, content_contains: str = None):
    """Assert that a message was sent by the bot."""
    assert len(bot.sent_messages) > 0
    if content_contains:
        last_message = bot.sent_messages[-1]
        assert content_contains in (last_message['content'] or '')

async def wait_for_task_completion(task_id: str, db: MockDatabase, timeout: float = 5.0):
    """Wait for a task to complete."""
    start_time = asyncio.get_event_loop().time()
    while True:
        task = await db.get_task(task_id)
        if task and task['status'] in ['completed', 'failed']:
            return task
        
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
        
        await asyncio.sleep(0.1)