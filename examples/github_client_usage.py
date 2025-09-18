# examples/github_client_usage.py
"""
Example usage of the GitHub Client for Backend Agent operations
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append('.')

from agents.backend.github_client import GitHubClient, sanitize_branch_name, generate_pr_description

async def github_client_example():
    """
    Example of how to use the GitHub Client for backend development tasks
    """
    print("🐙 GitHub Client Usage Example")
    print("=" * 40)
    
    # Initialize GitHub client
    github_client = GitHubClient()
    print(f"Repository: {github_client.github_repo}")
    
    # Example 1: Branch name sanitization
    print("\n1. Branch Name Sanitization:")
    test_names = [
        "Create user API endpoints!",
        "Fix bug in authentication system",
        "Add data validation & error handling",
        "Implement OAuth2.0 integration"
    ]
    
    for name in test_names:
        sanitized = sanitize_branch_name(name)
        print(f"   '{name}' → '{sanitized}'")
    
    # Example 2: PR Description Generation
    print("\n2. PR Description Generation:")
    pr_description = generate_pr_description(
        task_title="Create User Management API",
        task_description="Implement CRUD operations for user management with proper validation and error handling",
        success_criteria=[
            "All endpoints handle GET, POST, PUT, DELETE requests",
            "Input validation is implemented",
            "Error responses are properly formatted",
            "Unit tests achieve >90% coverage"
        ],
        agent_name="backend-agent-alpha",
        execution_time=2.5
    )
    
    print("Generated PR description preview:")
    print(pr_description[:300] + "...")
    print(f"Total length: {len(pr_description)} characters")
    
    # Example 3: GitHub Client Operations (without token)
    print("\n3. GitHub Client Operations:")
    
    # Initialize (this will fail without token, which is expected)
    initialized = await github_client.initialize()
    print(f"   GitHub client initialized: {initialized}")
    
    if not initialized:
        print("   ⚠️  GitHub token not set - this is expected for demo")
        print("   📝 To enable GitHub integration:")
        print("      export GITHUB_TOKEN=your_personal_access_token")
        print("      export GITHUB_REPO=owner/repository")
    
    # Show stats regardless
    stats = github_client.get_stats()
    print(f"   Client stats: {stats}")
    
    # Example 4: Branch Creation (simulated)
    print("\n4. Branch Creation Example:")
    task_id = "12345678"
    description = "Create user authentication endpoints"
    branch_name = f"feature/backend-{task_id[:8]}-{sanitize_branch_name(description)}"
    print(f"   Task ID: {task_id}")
    print(f"   Description: {description}")
    print(f"   Generated branch: {branch_name}")
    
    # Example 5: File Operations (simulated)
    print("\n5. File Operations Example:")
    example_files = {
        "app/routes/auth.py": "# Authentication routes implementation",
        "app/models/user.py": "# User model with validation",
        "tests/test_auth.py": "# Unit tests for authentication"
    }
    
    print("   Files to be committed:")
    for file_path, content_preview in example_files.items():
        print(f"     {file_path}: {content_preview}")
    
    print("\n✅ GitHub Client example completed!")
    print("\n📚 Key Features:")
    print("   • Automatic branch creation with sanitized names")
    print("   • Comprehensive PR descriptions with task details")
    print("   • File content management and commits")
    print("   • Operation statistics and success tracking")
    print("   • Graceful error handling and logging")

if __name__ == "__main__":
    asyncio.run(github_client_example())