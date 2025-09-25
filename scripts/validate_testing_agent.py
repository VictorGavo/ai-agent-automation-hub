#!/usr/bin/env python3
"""
Testing Agent Validation Script

Validates that the Testing Agent is properly configured and can function correctly.
"""

import asyncio
import logging
import sys
import tempfile
import subprocess
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_dependencies():
    """Validate that required dependencies are available."""
    print("🔍 Validating Dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-cov", 
        "bandit",
        "flake8",
        "black",
        "discord.py",
        "asyncio"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies available")
    return True

async def validate_file_structure():
    """Validate that all required files exist."""
    print("\n📁 Validating File Structure...")
    
    required_files = [
        "agents/testing/__init__.py",
        "agents/testing/main.py", 
        "agents/testing/testing_agent.py",
        "agents/testing/test_runner.py",
        "agents/testing/Dockerfile"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

async def validate_imports():
    """Validate that all modules can be imported."""
    print("\n📦 Validating Module Imports...")
    
    modules_to_test = [
        ("agents.testing", "Testing module"),
        ("agents.testing.testing_agent", "TestingAgent class"),
        ("agents.testing.test_runner", "TestRunner class"),
    ]
    
    import_errors = []
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"   ✅ {description}")
        except ImportError as e:
            print(f"   ❌ {description} - Import Error: {e}")
            import_errors.append((module_name, str(e)))
    
    if import_errors:
        print(f"\n⚠️  Import errors found:")
        for module, error in import_errors:
            print(f"   {module}: {error}")
        return False
    
    print("✅ All modules import successfully")
    return True

async def validate_test_runner():
    """Validate test runner functionality."""
    print("\n🧪 Validating Test Runner...")
    
    try:
        from agents.testing.test_runner import TestRunner
        test_runner = TestRunner()
        
        # Create temporary test workspace
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "test_workspace"
            workspace.mkdir()
            
            # Create minimal test project
            await create_minimal_test_project(workspace)
            
            print("   🔄 Running quick test validation...")
            
            # Run quick tests
            results = await test_runner.run_quick_tests(workspace)
            
            if results["overall_status"] in ["pass", "skip"]:
                print("   ✅ Test runner functional")
                print(f"      Duration: {results.get('duration', 0):.2f}s")
                print(f"      Categories: {len(results.get('categories', {}))}")
                return True
            else:
                print(f"   ❌ Test runner failed: {results.get('error', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"   ❌ Test runner validation failed: {e}")
        return False

async def create_minimal_test_project(workspace: Path):
    """Create a minimal test project for validation."""
    
    # Create simple Python file
    main_file = workspace / "main.py"
    main_file.write_text("""
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
""")
    
    # Create test file
    tests_dir = workspace / "tests"
    tests_dir.mkdir()
    
    test_file = tests_dir / "test_main.py"
    test_file.write_text("""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import hello

def test_hello():
    assert hello() == "Hello, World!"
""")

async def validate_docker_configuration():
    """Validate Docker configuration."""
    print("\n🐳 Validating Docker Configuration...")
    
    dockerfile_path = project_root / "agents/testing/Dockerfile"
    docker_compose_path = project_root / "docker-compose.yml"
    
    # Check Dockerfile
    if dockerfile_path.exists():
        print("   ✅ Testing Agent Dockerfile exists")
        
        # Check Dockerfile content
        content = dockerfile_path.read_text()
        required_elements = [
            "FROM python",
            "WORKDIR /app",
            "COPY requirements.txt",
            "RUN pip install",
            "CMD [\"python\", \"agents/testing/main.py\"]"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element.lower() not in content.lower():
                missing_elements.append(element)
        
        if missing_elements:
            print(f"   ⚠️  Dockerfile missing elements: {missing_elements}")
        else:
            print("   ✅ Dockerfile properly configured")
    else:
        print("   ❌ Testing Agent Dockerfile missing")
        return False
    
    # Check docker-compose.yml
    if docker_compose_path.exists():
        content = docker_compose_path.read_text()
        if "testing-agent:" in content:
            print("   ✅ Testing Agent configured in docker-compose.yml")
        else:
            print("   ❌ Testing Agent not found in docker-compose.yml")
            return False
    else:
        print("   ❌ docker-compose.yml missing")
        return False
    
    return True

async def validate_discord_integration():
    """Validate Discord command integration."""
    print("\n💬 Validating Discord Integration...")
    
    commands_file = project_root / "agents/orchestrator/commands.py"
    
    if not commands_file.exists():
        print("   ❌ Discord commands file missing")
        return False
    
    content = commands_file.read_text()
    
    # Check for testing commands
    testing_commands = [
        "test-pr",
        "test-status", 
        "test-config",
        "test-logs"
    ]
    
    missing_commands = []
    for cmd in testing_commands:
        if cmd not in content:
            missing_commands.append(cmd)
    
    if missing_commands:
        print(f"   ⚠️  Missing Discord commands: {missing_commands}")
        return False
    else:
        print("   ✅ All testing Discord commands present")
        return True

async def validate_environment_variables():
    """Validate required environment variables."""
    print("\n🔧 Validating Environment Configuration...")
    
    required_env_vars = [
        ("GITHUB_TOKEN", "GitHub API access"),
        ("DISCORD_BOT_TOKEN", "Discord bot integration"),
    ]
    
    optional_env_vars = [
        ("TESTING_POLLING_INTERVAL", "Test polling frequency"),
        ("TESTING_AUTO_APPROVE", "Auto-approval setting"),
        ("DATABASE_URL", "Database connection"),
    ]
    
    missing_required = []
    
    # Check required variables
    for var_name, description in required_env_vars:
        if os.getenv(var_name):
            print(f"   ✅ {var_name} - {description}")
        else:
            print(f"   ❌ {var_name} - {description} (Required)")
            missing_required.append(var_name)
    
    # Check optional variables
    for var_name, description in optional_env_vars:
        if os.getenv(var_name):
            print(f"   ✅ {var_name} - {description}")
        else:
            print(f"   ⚠️  {var_name} - {description} (Optional)")
    
    if missing_required:
        print(f"\n⚠️  Missing required environment variables: {missing_required}")
        print("Set these before running the testing agent")
        return False
    
    return True

async def run_comprehensive_validation():
    """Run all validation checks."""
    print("🎯 Testing Agent Comprehensive Validation")
    print("=" * 60)
    
    validations = [
        ("Dependencies", validate_dependencies),
        ("File Structure", validate_file_structure),
        ("Module Imports", validate_imports),
        ("Test Runner", validate_test_runner),
        ("Docker Configuration", validate_docker_configuration),
        ("Discord Integration", validate_discord_integration),
        ("Environment Variables", validate_environment_variables),
    ]
    
    results = {}
    
    for name, validation_func in validations:
        try:
            result = await validation_func()
            results[name] = result
        except Exception as e:
            print(f"   ❌ {name} validation failed with error: {e}")
            results[name] = False
    
    # Summary
    print("\n📊 Validation Summary")
    print("=" * 30)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 Testing Agent is ready for deployment!")
        print("\nNext steps:")
        print("1. Build with: docker-compose build testing-agent")
        print("2. Run with: docker-compose up testing-agent")
        print("3. Test Discord commands in your server")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please fix the issues above.")
        return False

async def main():
    """Main validation function."""
    try:
        success = await run_comprehensive_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Validation failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())