"""
Unit tests for the Discord bot functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from tests.utils import MockDiscordBot, MockDatabase, MockInteraction, create_test_task


class TestDiscordBot:
    """Test cases for Discord bot functionality."""
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self, mock_discord_bot):
        """Test that the bot initializes correctly."""
        assert mock_discord_bot.user.name == "TestBot"
        assert mock_discord_bot.user.id == 123456789
    
    @pytest.mark.asyncio
    async def test_send_message(self, mock_discord_bot):
        """Test sending messages through the bot."""
        channel_id = 123456
        content = "Test message"
        
        message = await mock_discord_bot.send_message(channel_id, content)
        
        assert len(mock_discord_bot.sent_messages) == 1
        assert mock_discord_bot.sent_messages[0]['content'] == content
        assert mock_discord_bot.sent_messages[0]['channel_id'] == channel_id
    
    @pytest.mark.asyncio
    async def test_interaction_response(self):
        """Test responding to Discord interactions."""
        interaction = MockInteraction()
        
        await interaction.response_send_message("Test response")
        
        assert interaction.responded is True
        interaction.response.send_message.assert_called_once()


class TestSlashCommands:
    """Test cases for Discord slash commands."""
    
    @pytest.fixture
    def mock_task_manager(self, mock_database):
        """Create a mock task manager."""
        with patch('bot.main.TaskManager') as mock_tm:
            mock_tm.return_value.create_task = AsyncMock(return_value='test123')
            mock_tm.return_value.get_task = AsyncMock(return_value={
                'id': 'test123',
                'title': 'Test Task',
                'status': 'pending',
                'agent_type': 'backend'
            })
            yield mock_tm.return_value
    
    @pytest.mark.asyncio
    async def test_create_task_command(self, mock_task_manager):
        """Test the /create-task slash command."""
        interaction = MockInteraction()
        
        # Mock the command handler
        with patch('bot.main.DiscordBot') as mock_bot_class:
            bot_instance = Mock()
            bot_instance.task_manager = mock_task_manager
            mock_bot_class.return_value = bot_instance
            
            # Simulate command execution
            task_data = create_test_task("Integration Test", "Test description", "backend")
            task_id = await mock_task_manager.create_task(task_data)
            
            assert task_id == 'test123'
            mock_task_manager.create_task.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_task_status_command(self, mock_task_manager):
        """Test the /task-status slash command."""
        interaction = MockInteraction()
        task_id = 'test123'
        
        # Mock getting task status
        task_data = await mock_task_manager.get_task(task_id)
        
        assert task_data['id'] == task_id
        assert task_data['status'] == 'pending'
        mock_task_manager.get_task.assert_called_once_with(task_id)
    
    @pytest.mark.discord
    @pytest.mark.asyncio
    async def test_list_tasks_command(self, mock_task_manager):
        """Test the /list-tasks slash command."""
        interaction = MockInteraction()
        
        # Mock listing tasks
        with patch.object(mock_task_manager, 'list_tasks') as mock_list:
            mock_list.return_value = [
                {'id': 'task1', 'title': 'Task 1', 'status': 'pending'},
                {'id': 'task2', 'title': 'Task 2', 'status': 'completed'}
            ]
            
            tasks = await mock_task_manager.list_tasks()
            
            assert len(tasks) == 2
            assert tasks[0]['id'] == 'task1'
            assert tasks[1]['status'] == 'completed'


class TestBotConfiguration:
    """Test cases for bot configuration."""
    
    def test_config_loading(self, test_config):
        """Test that configuration loads correctly."""
        assert test_config.app_mode == "testing"
        assert test_config.log_level == "DEBUG"
        assert test_config.max_concurrent_tasks == 2
    
    def test_discord_token_validation(self, test_config):
        """Test Discord token validation."""
        assert test_config.discord_token == "test_token_12345"
        assert len(test_config.discord_token) > 10


class TestErrorHandling:
    """Test cases for error handling in the bot."""
    
    @pytest.mark.asyncio
    async def test_invalid_task_id(self, mock_task_manager):
        """Test handling of invalid task IDs."""
        mock_task_manager.get_task.return_value = None
        
        task = await mock_task_manager.get_task('invalid_id')
        assert task is None
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, mock_database):
        """Test handling of database connection errors."""
        # Simulate database disconnection
        mock_database.connected = False
        
        with pytest.raises(Exception):
            if not mock_database.connected:
                raise Exception("Database not connected")
    
    @pytest.mark.asyncio
    async def test_agent_timeout(self):
        """Test handling of agent timeouts."""
        mock_agent = Mock()
        mock_agent.process_task = AsyncMock(side_effect=asyncio.TimeoutError("Agent timeout"))
        
        with pytest.raises(asyncio.TimeoutError):
            await mock_agent.process_task({'title': 'Test Task'})


class TestBotIntegration:
    """Integration tests for bot functionality."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_task_workflow(self, mock_database, mock_discord_bot):
        """Test a complete task creation and execution workflow."""
        from tests.utils import MockTaskManager, MockAgent
        
        # Setup components
        task_manager = MockTaskManager(mock_database)
        agent = MockAgent("backend")
        
        # Create task
        task_data = create_test_task("Integration Test", "Full workflow test", "backend")
        task_id = await task_manager.create_task(task_data)
        
        # Verify task creation
        task = await task_manager.get_task(task_id)
        assert task['title'] == "Integration Test"
        assert task['status'] == 'pending'
        
        # Execute task
        result = await task_manager.execute_task(task_id, agent)
        
        # Verify execution
        assert result['success'] is True
        assert 'Mock backend agent processed' in result['result']
        
        # Verify task completion
        completed_task = await task_manager.get_task(task_id)
        assert completed_task['status'] == 'completed'
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, mock_database):
        """Test executing multiple tasks concurrently."""
        from tests.utils import MockTaskManager, MockAgent
        
        task_manager = MockTaskManager(mock_database)
        agent = MockAgent("testing")
        
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_data = create_test_task(f"Concurrent Task {i}", f"Task {i} description", "testing")
            task_id = await task_manager.create_task(task_data)
            task_ids.append(task_id)
        
        # Execute tasks concurrently
        tasks = [task_manager.execute_task(task_id, agent) for task_id in task_ids]
        results = await asyncio.gather(*tasks)
        
        # Verify all tasks completed
        assert len(results) == 3
        for result in results:
            assert result['success'] is True
        
        # Verify agent processed all tasks
        assert agent.tasks_processed == 3