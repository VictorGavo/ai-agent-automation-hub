#!/usr/bin/env python3
"""
Testing Agent Example Script

Demonstrates how to use the Testing Agent programmatically
and showcase its capabilities.
"""

import asyncio
import logging
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.testing.testing_agent import TestingAgent
from agents.testing.test_runner import TestRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_test_runner():
    """Demonstrate the test runner capabilities."""
    print("🧪 Testing Agent Demo - Test Runner")
    print("=" * 50)
    
    # Create a sample project for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "sample_project"
        workspace.mkdir()
        
        # Create sample files
        await create_sample_project(workspace)
        
        # Initialize test runner
        test_runner = TestRunner()
        
        print(f"📁 Created sample project in: {workspace}")
        print("🔄 Running comprehensive tests...")
        
        # Run comprehensive tests
        results = await test_runner.run_comprehensive_tests(workspace)
        
        print("\n📊 Test Results:")
        print(f"Overall Status: {results['overall_status']}")
        print(f"Duration: {results['duration']:.2f}s")
        
        for category, result in results['categories'].items():
            status_emoji = "✅" if result['status'] == 'pass' else "❌" if result['status'] == 'fail' else "⏭️"
            print(f"{status_emoji} {category.title()}: {result['status']}")
            if 'details' in result:
                print(f"   └─ {result['details']}")
        
        if 'coverage' in results:
            print(f"📈 Code Coverage: {results['coverage'].get('percentage', 'N/A')}%")

async def create_sample_project(workspace: Path):
    """Create a sample Python project for testing."""
    
    # Create main module
    main_py = workspace / "main.py"
    main_py.write_text("""
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b

def divide(a, b):
    \"\"\"Divide two numbers.\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def vulnerable_function(user_input):
    \"\"\"This function has a security vulnerability.\"\"\"
    # This is intentionally vulnerable for demo purposes
    return eval(user_input)  # nosec - demo only

if __name__ == "__main__":
    print(f"2 + 3 = {add(2, 3)}")
    print(f"10 / 2 = {divide(10, 2)}")
""")
    
    # Create test file
    tests_dir = workspace / "tests"
    tests_dir.mkdir()
    
    test_main = tests_dir / "test_main.py"
    test_main.write_text("""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import add, divide

def test_add():
    \"\"\"Test the add function.\"\"\"
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_divide():
    \"\"\"Test the divide function.\"\"\"
    assert divide(10, 2) == 5
    assert divide(9, 3) == 3
    
def test_divide_by_zero():
    \"\"\"Test division by zero raises error.\"\"\"
    with pytest.raises(ValueError):
        divide(10, 0)

def test_edge_cases():
    \"\"\"Test edge cases.\"\"\"
    assert add(1.5, 2.5) == 4.0
    assert divide(1, 3) == pytest.approx(0.3333, rel=1e-3)
""")
    
    # Create requirements.txt
    requirements = workspace / "requirements.txt"
    requirements.write_text("""
pytest>=7.0.0
pytest-cov>=4.0.0
""")
    
    # Create setup.py
    setup_py = workspace / "setup.py"
    setup_py.write_text("""
from setuptools import setup, find_packages

setup(
    name="sample-project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
    ],
)
""")

async def demo_testing_agent_status():
    """Demonstrate testing agent status capabilities."""
    print("\n🤖 Testing Agent Demo - Status")
    print("=" * 50)
    
    try:
        # Initialize testing agent (without starting main loop)
        testing_agent = TestingAgent()
        
        # Get status
        status = await testing_agent.get_status()
        
        print("📊 Testing Agent Status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error getting testing agent status: {e}")

def print_testing_commands():
    """Print available Discord testing commands."""
    print("\n💬 Testing Agent Discord Commands")
    print("=" * 50)
    
    commands = [
        ("/test-pr <pr_number>", "Run tests on a specific pull request"),
        ("/test-status", "Get current testing agent status and recent results"),
        ("/test-config", "Configure testing agent settings (auto-approve, polling)"),
        ("/test-logs", "Get recent testing agent logs"),
    ]
    
    print("Available Discord slash commands:")
    for cmd, desc in commands:
        print(f"   {cmd:<25} - {desc}")

def print_features():
    """Print testing agent features."""
    print("\n🚀 Testing Agent Features")
    print("=" * 50)
    
    features = [
        "🔍 Automatic PR monitoring and testing",
        "🧪 Comprehensive test suite execution (pytest)",
        "🔒 Security scanning with bandit",
        "📊 Code coverage analysis",
        "🎨 Code style checks (flake8, black)",
        "⚡ Integration test support",
        "📈 Performance benchmarking",
        "🤖 Automatic PR approval for passing tests",
        "💬 Discord notifications for test results",
        "🐳 Dockerized deployment",
        "📱 Mobile-friendly Discord integration"
    ]
    
    print("Key Features:")
    for feature in features:
        print(f"   {feature}")

async def main():
    """Main demo function."""
    print("🎉 AI Agent Automation Hub - Testing Agent Demo")
    print("=" * 60)
    
    # Print features
    print_features()
    
    # Print Discord commands
    print_testing_commands()
    
    # Demo test runner
    try:
        await demo_test_runner()
    except Exception as e:
        print(f"❌ Test runner demo failed: {e}")
    
    # Demo testing agent status
    try:
        await demo_testing_agent_status()
    except Exception as e:
        print(f"❌ Testing agent status demo failed: {e}")
    
    print("\n✅ Testing Agent Demo Complete!")
    print("\nTo use the Testing Agent:")
    print("1. Build and run with Docker: docker-compose up testing-agent")
    print("2. Use Discord commands to interact with the testing system")
    print("3. Monitor test results in real-time")
    print("4. Configure auto-approval settings as needed")

if __name__ == "__main__":
    asyncio.run(main())