"""
Unit tests for the AI agents functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from tests.utils import MockAgent, MockDatabase, create_test_task


class TestBackendAgent:
    """Test cases for the Backend Agent."""
    
    @pytest.fixture
    def backend_agent(self):
        """Create a backend agent for testing."""
        return MockAgent("backend")
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, backend_agent):
        """Test that the backend agent initializes correctly."""
        assert backend_agent.agent_type == "backend"
        assert backend_agent.status == "healthy"
        assert backend_agent.tasks_processed == 0
    
    @pytest.mark.asyncio
    async def test_process_simple_task(self, backend_agent):
        """Test processing a simple backend task."""
        task_data = create_test_task("Create API endpoint", "Create a REST API endpoint for user management", "backend")
        
        result = await backend_agent.mock_process_task(task_data)
        
        assert result['success'] is True
        assert 'Mock backend agent processed' in result['result']
        assert result['metadata']['agent_type'] == 'backend'
        assert backend_agent.tasks_processed == 1
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, backend_agent):
        """Test agent health check functionality."""
        health_status = await backend_agent.health_check()
        assert health_status is True
    
    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, backend_agent):
        """Test that the agent can handle concurrent tasks."""
        tasks = []
        for i in range(3):
            task_data = create_test_task(f"Task {i}", f"Description {i}", "backend")
            tasks.append(backend_agent.mock_process_task(task_data))
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert result['success'] is True
        assert backend_agent.tasks_processed == 3


class TestTestingAgent:
    """Test cases for the Testing Agent."""
    
    @pytest.fixture
    def testing_agent(self):
        """Create a testing agent for testing."""
        return MockAgent("testing")
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, testing_agent):
        """Test that the testing agent initializes correctly."""
        assert testing_agent.agent_type == "testing"
        assert testing_agent.status == "healthy"
    
    @pytest.mark.asyncio
    async def test_process_test_task(self, testing_agent):
        """Test processing a testing-related task."""
        task_data = create_test_task("Write unit tests", "Create unit tests for the user service", "testing")
        
        result = await testing_agent.mock_process_task(task_data)
        
        assert result['success'] is True
        assert 'Mock testing agent processed' in result['result']
        assert result['metadata']['agent_type'] == 'testing'
    
    @pytest.mark.asyncio
    async def test_agent_status_tracking(self, testing_agent):
        """Test that agent status is tracked correctly."""
        initial_status = testing_agent.get_status()
        assert initial_status == "healthy"
        
        # Process a task
        task_data = create_test_task("Run integration tests", "Execute integration test suite", "testing")
        await testing_agent.mock_process_task(task_data)
        
        # Status should remain healthy
        final_status = testing_agent.get_status()
        assert final_status == "healthy"


class TestOrchestrator:
    """Test cases for the Orchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator for testing."""
        return MockAgent("orchestrator")
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test that the orchestrator initializes correctly."""
        assert orchestrator.agent_type == "orchestrator"
        assert orchestrator.status == "healthy"
    
    @pytest.mark.asyncio
    async def test_task_coordination(self, orchestrator):
        """Test orchestrator task coordination."""
        task_data = create_test_task("Coordinate deployment", "Coordinate multi-service deployment", "orchestrator")
        
        result = await orchestrator.mock_process_task(task_data)
        
        assert result['success'] is True
        assert 'Mock orchestrator agent processed' in result['result']
        assert result['metadata']['agent_type'] == 'orchestrator'


class TestAgentErrorHandling:
    """Test cases for agent error handling."""
    
    @pytest.fixture
    def error_agent(self):
        """Create an agent that will produce errors for testing."""
        agent = MockAgent("backend")
        # Override the process_task method to simulate errors
        agent.process_task = AsyncMock(side_effect=Exception("Simulated agent error"))
        return agent
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, error_agent):
        """Test that agent errors are handled properly."""
        task_data = create_test_task("Failing task", "This task will fail", "backend")
        
        with pytest.raises(Exception) as exc_info:
            await error_agent.process_task(task_data)
        
        assert "Simulated agent error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self):
        """Test handling of agent timeouts."""
        agent = MockAgent("backend")
        
        # Create a task that times out
        async def timeout_task(task_data):
            await asyncio.sleep(10)  # Simulate long-running task
            return {'success': True}
        
        agent.process_task = timeout_task
        
        # Test with a short timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                agent.process_task(create_test_task("Long task", "This will timeout", "backend")),
                timeout=0.1
            )
    
    @pytest.mark.asyncio
    async def test_agent_recovery(self):
        """Test agent recovery after errors."""
        agent = MockAgent("backend")
        
        # First, make it fail
        agent.process_task = AsyncMock(side_effect=Exception("Temporary failure"))
        
        with pytest.raises(Exception):
            await agent.process_task(create_test_task("Failing task", "Will fail", "backend"))
        
        # Then, make it work again
        agent.process_task = AsyncMock(return_value={'success': True, 'result': 'Recovered!'})
        
        result = await agent.process_task(create_test_task("Recovery task", "Should work", "backend"))
        assert result['success'] is True
        assert result['result'] == 'Recovered!'


class TestAgentIntegration:
    """Integration tests for agents working together."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self, mock_database):
        """Test a workflow involving multiple agents."""
        from tests.utils import MockTaskManager
        
        # Create agents
        backend_agent = MockAgent("backend")
        testing_agent = MockAgent("testing")
        orchestrator = MockAgent("orchestrator")
        
        # Create task manager
        task_manager = MockTaskManager(mock_database)
        
        # Create tasks for different agents
        backend_task_data = create_test_task("Create service", "Create user service", "backend")
        testing_task_data = create_test_task("Test service", "Test user service", "testing")
        orchestrator_task_data = create_test_task("Deploy service", "Deploy user service", "orchestrator")
        
        # Execute tasks in sequence
        backend_task_id = await task_manager.create_task(backend_task_data)
        backend_result = await task_manager.execute_task(backend_task_id, backend_agent)
        assert backend_result['success'] is True
        
        testing_task_id = await task_manager.create_task(testing_task_data)
        testing_result = await task_manager.execute_task(testing_task_id, testing_agent)
        assert testing_result['success'] is True
        
        orchestrator_task_id = await task_manager.create_task(orchestrator_task_data)
        orchestrator_result = await task_manager.execute_task(orchestrator_task_id, orchestrator)
        assert orchestrator_result['success'] is True
        
        # Verify all agents processed their tasks
        assert backend_agent.tasks_processed == 1
        assert testing_agent.tasks_processed == 1
        assert orchestrator.tasks_processed == 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_load_balancing(self, mock_database):
        """Test load balancing across multiple agents of the same type."""
        from tests.utils import MockTaskManager
        
        # Create multiple backend agents
        backend_agents = [MockAgent("backend") for _ in range(3)]
        task_manager = MockTaskManager(mock_database)
        
        # Create multiple tasks
        tasks = []
        for i in range(6):
            task_data = create_test_task(f"Load test task {i}", f"Task {i} for load testing", "backend")
            task_id = await task_manager.create_task(task_data)
            tasks.append(task_id)
        
        # Distribute tasks across agents (simple round-robin)
        results = []
        for i, task_id in enumerate(tasks):
            agent = backend_agents[i % len(backend_agents)]
            result = await task_manager.execute_task(task_id, agent)
            results.append(result)
        
        # Verify all tasks completed successfully
        assert len(results) == 6
        for result in results:
            assert result['success'] is True
        
        # Verify load distribution
        tasks_per_agent = [agent.tasks_processed for agent in backend_agents]
        assert sum(tasks_per_agent) == 6
        assert all(count >= 1 for count in tasks_per_agent)  # Each agent got at least one task