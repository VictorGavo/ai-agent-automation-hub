# examples/task_executor_usage.py
"""
Example usage of the TaskExecutor for Flask development tasks
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append('.')

from agents.backend.task_executor import TaskExecutor
from database.models.task import Task, TaskCategory

class MockTask:
    """Mock task for demonstration"""
    def __init__(self, task_id, title, description, success_criteria=None, task_metadata=None):
        self.id = task_id
        self.title = title
        self.description = description
        self.success_criteria = success_criteria or []
        self.task_metadata = task_metadata or {}
        self.category = TaskCategory.BACKEND

async def task_executor_example():
    """
    Example of how to use the TaskExecutor for various backend development tasks
    """
    print("🔧 TaskExecutor Usage Example")
    print("=" * 40)
    
    # Initialize TaskExecutor
    executor = TaskExecutor("demo-agent")
    print(f"TaskExecutor initialized for: {executor.agent_name}")
    print(f"Project root: {executor.project_root}")
    
    # Example 1: Flask Endpoint Creation
    print("\n1. Flask Endpoint Creation:")
    flask_task = MockTask(
        task_id="flask-001",
        title="Create User Management API",
        description="Create POST /api/users endpoint for user registration with validation",
        success_criteria=[
            "Endpoint handles POST requests to /api/users",
            "Input validation for required fields",
            "Returns appropriate JSON responses",
            "Includes error handling for invalid data"
        ],
        task_metadata={
            "route": "/api/users",
            "method": "POST",
            "requires_auth": False,
            "requires_db": True,
            "request_schema": {
                "username": "string",
                "email": "string",
                "password": "string"
            }
        }
    )
    
    print(f"Task: {flask_task.title}")
    print(f"Description: {flask_task.description}")
    
    # Execute Flask endpoint task
    result = await executor.execute_flask_endpoint(flask_task)
    
    if result["success"]:
        impl = result["implementation"]
        print(f"✅ Success! Created {len(impl['files'])} files:")
        for file_path in impl["files"].keys():
            print(f"   - {file_path}")
        print(f"   Route: {impl['route_path']} ({impl['http_method']})")
        print(f"   Function: {impl['function_name']}")
        print(f"   Validation passed: {impl['validation_passed']}")
        
        # Show sample code snippet
        route_file = list(impl["files"].keys())[0]
        code_sample = impl["files"][route_file][:300] + "..."
        print(f"\\n   Code sample from {route_file}:")
        print(f"   {code_sample}")
    else:
        print(f"❌ Failed: {result['message']}")
    
    # Example 2: Code Generation
    print("\n2. Flask Code Generation:")
    endpoint_spec = {
        "route": "/api/auth/login",
        "method": "POST",
        "function_name": "user_login",
        "description": "Authenticate user login",
        "requires_auth": False,
        "requires_db": True,
        "request_schema": {"username": "string", "password": "string"},
        "response_schema": {"token": "string", "user_id": "integer"}
    }
    
    flask_code = await executor.generate_flask_code(endpoint_spec)
    print(f"Generated Flask code for {endpoint_spec['route']}:")
    print(f"Length: {len(flask_code)} characters")
    print(f"Function: {endpoint_spec['function_name']}")
    
    # Example 3: Code Validation
    print("\n3. Code Validation:")
    validation_task = MockTask(
        task_id="validate-001",
        title="Validate Implementation",
        description="Check if code meets requirements",
        success_criteria=[
            "Code has proper error handling",
            "Uses appropriate Flask patterns",
            "Includes input validation"
        ]
    )
    
    sample_code = '''
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint with proper structure"""
    try:
        result = {
            "success": True,
            "message": "Test endpoint working",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
'''
    
    validation_result = await executor.validate_implementation(validation_task, sample_code)
    print(f"Validation result: {'✅ PASSED' if validation_result else '❌ FAILED'}")
    
    # Example 4: Test Execution (simulated)
    print("\n4. Test Execution:")
    test_files = ["tests/test_users.py", "tests/test_auth.py"]
    test_results = await executor.run_tests(test_files)
    
    print(f"Tests executed: {test_results['tests_executed']}")
    print(f"All tests passed: {test_results['all_tests_passed']}")
    print(f"New tests passed: {test_results['new_tests_passed']}")
    
    if test_results['test_output']:
        output_preview = test_results['test_output'][:200] + "..." if len(test_results['test_output']) > 200 else test_results['test_output']
        print(f"Test output preview: {output_preview}")
    
    # Example 5: Statistics and Performance
    print("\n5. TaskExecutor Statistics:")
    stats = executor.get_stats()
    task_stats = stats["task_executor_stats"]
    
    print(f"Tasks executed: {task_stats['tasks_executed']}")
    print(f"Endpoints created: {task_stats['endpoints_created']}")
    print(f"Tests generated: {task_stats['tests_generated']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    
    if task_stats['execution_errors'] > 0:
        print(f"Execution errors: {task_stats['execution_errors']}")
    if task_stats['validation_failures'] > 0:
        print(f"Validation failures: {task_stats['validation_failures']}")
    
    print("\n✅ TaskExecutor example completed!")
    print("\n📚 Key Features Demonstrated:")
    print("   • Flask endpoint creation with full code generation")
    print("   • Comprehensive test case generation")
    print("   • Code validation against success criteria")
    print("   • Error handling and input validation")
    print("   • Statistical tracking and performance monitoring")
    print("   • Flexible task parsing and requirement extraction")

if __name__ == "__main__":
    asyncio.run(task_executor_example())