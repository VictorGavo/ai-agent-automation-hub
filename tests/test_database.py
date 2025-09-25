"""
Unit tests for database functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from tests.utils import MockDatabase, create_test_task


class TestDatabaseOperations:
    """Test cases for basic database operations."""
    
    @pytest.mark.asyncio
    async def test_database_connection(self, mock_database):
        """Test database connection."""
        assert mock_database.connected is True
    
    @pytest.mark.asyncio
    async def test_create_task(self, mock_database):
        """Test creating a task in the database."""
        task_data = create_test_task("Test Task", "Test Description", "backend")
        task_id = await mock_database.create_task(task_data)
        
        assert task_id is not None
        assert len(task_id) == 8  # UUID prefix length
        assert task_id in mock_database.tasks
    
    @pytest.mark.asyncio
    async def test_get_task(self, mock_database):
        """Test retrieving a task from the database."""
        # Create a task first
        task_data = create_test_task("Get Test Task", "Description for get test", "testing")
        task_id = await mock_database.create_task(task_data)
        
        # Retrieve the task
        retrieved_task = await mock_database.get_task(task_id)
        
        assert retrieved_task is not None
        assert retrieved_task['id'] == task_id
        assert retrieved_task['title'] == "Get Test Task"
        assert retrieved_task['description'] == "Description for get test"
        assert retrieved_task['agent_type'] == "testing"
        assert retrieved_task['status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, mock_database):
        """Test retrieving a task that doesn't exist."""
        retrieved_task = await mock_database.get_task("nonexistent")
        assert retrieved_task is None
    
    @pytest.mark.asyncio
    async def test_update_task(self, mock_database):
        """Test updating a task in the database."""
        # Create a task first
        task_data = create_test_task("Update Test Task", "Original description", "backend")
        task_id = await mock_database.create_task(task_data)
        
        # Update the task
        updates = {
            'status': 'completed',
            'result': 'Task completed successfully'
        }
        success = await mock_database.update_task(task_id, updates)
        
        assert success is True
        
        # Verify the update
        updated_task = await mock_database.get_task(task_id)
        assert updated_task['status'] == 'completed'
        assert updated_task['result'] == 'Task completed successfully'
        assert updated_task['updated_at'] > updated_task['created_at']
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, mock_database):
        """Test updating a task that doesn't exist."""
        updates = {'status': 'completed'}
        success = await mock_database.update_task("nonexistent", updates)
        assert success is False


class TestTaskListing:
    """Test cases for task listing functionality."""
    
    @pytest.mark.asyncio
    async def test_list_all_tasks(self, mock_database):
        """Test listing all tasks."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_data = create_test_task(f"List Test Task {i}", f"Description {i}", "backend")
            task_id = await mock_database.create_task(task_data)
            task_ids.append(task_id)
        
        # List all tasks
        all_tasks = await mock_database.list_tasks()
        
        assert len(all_tasks) == 3
        retrieved_ids = [task['id'] for task in all_tasks]
        for task_id in task_ids:
            assert task_id in retrieved_ids
    
    @pytest.mark.asyncio
    async def test_list_tasks_by_status(self, mock_database):
        """Test listing tasks filtered by status."""
        # Create tasks with different statuses
        task_data_1 = create_test_task("Pending Task", "Pending description", "backend")
        task_id_1 = await mock_database.create_task(task_data_1)
        
        task_data_2 = create_test_task("Completed Task", "Completed description", "testing")
        task_id_2 = await mock_database.create_task(task_data_2)
        await mock_database.update_task(task_id_2, {'status': 'completed'})
        
        # List pending tasks
        pending_tasks = await mock_database.list_tasks({'status': 'pending'})
        assert len(pending_tasks) == 1
        assert pending_tasks[0]['id'] == task_id_1
        
        # List completed tasks
        completed_tasks = await mock_database.list_tasks({'status': 'completed'})
        assert len(completed_tasks) == 1
        assert completed_tasks[0]['id'] == task_id_2
    
    @pytest.mark.asyncio
    async def test_list_tasks_by_agent_type(self, mock_database):
        """Test listing tasks filtered by agent type."""
        # Create tasks for different agent types
        backend_task_data = create_test_task("Backend Task", "Backend description", "backend")
        backend_task_id = await mock_database.create_task(backend_task_data)
        
        testing_task_data = create_test_task("Testing Task", "Testing description", "testing")
        testing_task_id = await mock_database.create_task(testing_task_data)
        
        # List backend tasks
        backend_tasks = await mock_database.list_tasks({'agent_type': 'backend'})
        assert len(backend_tasks) == 1
        assert backend_tasks[0]['id'] == backend_task_id
        
        # List testing tasks
        testing_tasks = await mock_database.list_tasks({'agent_type': 'testing'})
        assert len(testing_tasks) == 1
        assert testing_tasks[0]['id'] == testing_task_id
    
    @pytest.mark.asyncio
    async def test_list_tasks_multiple_filters(self, mock_database):
        """Test listing tasks with multiple filters."""
        # Create various tasks
        tasks_data = [
            ("Backend Pending", "backend", "pending"),
            ("Backend Completed", "backend", "completed"),
            ("Testing Pending", "testing", "pending"),
            ("Testing Completed", "testing", "completed"),
        ]
        
        created_tasks = []
        for title, agent_type, status in tasks_data:
            task_data = create_test_task(title, f"{title} description", agent_type)
            task_id = await mock_database.create_task(task_data)
            if status != "pending":
                await mock_database.update_task(task_id, {'status': status})
            created_tasks.append((task_id, agent_type, status))
        
        # Filter by agent_type and status
        backend_pending = await mock_database.list_tasks({
            'agent_type': 'backend',
            'status': 'pending'
        })
        assert len(backend_pending) == 1
        assert backend_pending[0]['agent_type'] == 'backend'
        assert backend_pending[0]['status'] == 'pending'


class TestLogging:
    """Test cases for logging functionality."""
    
    @pytest.mark.asyncio
    async def test_log_event(self, mock_database):
        """Test logging events to the database."""
        event_data = {
            'event_type': 'task_created',
            'task_id': 'test_task_123',
            'message': 'New task created successfully'
        }
        
        await mock_database.log_event(event_data)
        
        assert len(mock_database.logs) == 1
        logged_event = mock_database.logs[0]
        assert logged_event['event_type'] == 'task_created'
        assert logged_event['task_id'] == 'test_task_123'
        assert logged_event['message'] == 'New task created successfully'
        assert 'timestamp' in logged_event
    
    @pytest.mark.asyncio
    async def test_multiple_log_entries(self, mock_database):
        """Test logging multiple events."""
        events = [
            {'event_type': 'task_created', 'message': 'Task 1 created'},
            {'event_type': 'task_started', 'message': 'Task 1 started'},
            {'event_type': 'task_completed', 'message': 'Task 1 completed'},
        ]
        
        for event in events:
            await mock_database.log_event(event)
        
        assert len(mock_database.logs) == 3
        for i, logged_event in enumerate(mock_database.logs):
            assert logged_event['event_type'] == events[i]['event_type']
            assert logged_event['message'] == events[i]['message']


class TestAgentManagement:
    """Test cases for agent management in the database."""
    
    @pytest.mark.asyncio
    async def test_get_agent_status(self, mock_database):
        """Test getting agent status from the database."""
        # Get status for existing agents
        backend_status = await mock_database.get_agent_status('backend')
        assert backend_status is not None
        assert backend_status['id'] == 'backend'
        assert backend_status['name'] == 'Backend Agent'
        assert backend_status['status'] == 'healthy'
        
        testing_status = await mock_database.get_agent_status('testing')
        assert testing_status is not None
        assert testing_status['id'] == 'testing'
        assert testing_status['name'] == 'Testing Agent'
        assert testing_status['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_agent_status(self, mock_database):
        """Test getting status for a non-existent agent."""
        status = await mock_database.get_agent_status('nonexistent')
        assert status is None
    
    @pytest.mark.asyncio
    async def test_agent_heartbeat_tracking(self, mock_database):
        """Test that agent heartbeats are tracked."""
        # All agents should have recent heartbeats
        for agent_id in ['backend', 'testing', 'orchestrator']:
            agent_status = await mock_database.get_agent_status(agent_id)
            assert agent_status is not None
            
            # Heartbeat should be recent (within the last minute)
            time_diff = datetime.now() - agent_status['last_heartbeat']
            assert time_diff < timedelta(minutes=1)


class TestDatabasePerformance:
    """Test cases for database performance and concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_creation(self, mock_database):
        """Test creating multiple tasks concurrently."""
        async def create_task_async(i):
            task_data = create_test_task(f"Concurrent Task {i}", f"Description {i}", "backend")
            return await mock_database.create_task(task_data)
        
        # Create 5 tasks concurrently
        tasks = [create_task_async(i) for i in range(5)]
        task_ids = await asyncio.gather(*tasks)
        
        assert len(task_ids) == 5
        assert len(set(task_ids)) == 5  # All IDs should be unique
        
        # Verify all tasks exist
        all_tasks = await mock_database.list_tasks()
        assert len(all_tasks) == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_task_updates(self, mock_database):
        """Test updating multiple tasks concurrently."""
        # Create tasks first
        task_ids = []
        for i in range(3):
            task_data = create_test_task(f"Update Concurrent Task {i}", f"Description {i}", "backend")
            task_id = await mock_database.create_task(task_data)
            task_ids.append(task_id)
        
        # Update all tasks concurrently
        async def update_task_async(task_id, status):
            return await mock_database.update_task(task_id, {'status': status})
        
        update_tasks = [
            update_task_async(task_ids[0], 'running'),
            update_task_async(task_ids[1], 'completed'),
            update_task_async(task_ids[2], 'failed'),
        ]
        
        results = await asyncio.gather(*update_tasks)
        assert all(results)  # All updates should succeed
        
        # Verify updates
        statuses = ['running', 'completed', 'failed']
        for i, task_id in enumerate(task_ids):
            task = await mock_database.get_task(task_id)
            assert task['status'] == statuses[i]
    
    @pytest.mark.asyncio
    async def test_large_task_list_performance(self, mock_database):
        """Test performance with a large number of tasks."""
        # Create a large number of tasks
        task_count = 50
        task_ids = []
        
        for i in range(task_count):
            agent_type = ['backend', 'testing', 'orchestrator'][i % 3]
            task_data = create_test_task(f"Performance Task {i}", f"Description {i}", agent_type)
            task_id = await mock_database.create_task(task_data)
            task_ids.append(task_id)
        
        # List all tasks - should be fast
        start_time = asyncio.get_event_loop().time()
        all_tasks = await mock_database.list_tasks()
        end_time = asyncio.get_event_loop().time()
        
        assert len(all_tasks) == task_count
        assert (end_time - start_time) < 1.0  # Should complete in less than 1 second
        
        # Filter tasks - should also be fast
        start_time = asyncio.get_event_loop().time()
        backend_tasks = await mock_database.list_tasks({'agent_type': 'backend'})
        end_time = asyncio.get_event_loop().time()
        
        expected_backend_count = (task_count + 2) // 3  # Every 3rd task starting from 0
        assert len(backend_tasks) == expected_backend_count
        assert (end_time - start_time) < 1.0