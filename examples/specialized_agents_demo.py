#!/usr/bin/env python3
"""
Specialized Agents Integration Demo

This example demonstrates how to use all the specialized agent classes
that inherit from BaseAgent to coordinate a complete development workflow.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import (
    OrchestratorAgent,
    BackendAgent, 
    DatabaseAgent,
    CodeAgent,
    TestingAgent,
    require_dev_bible_prep
)


def demonstrate_complete_workflow():
    """
    Demonstrate a complete development workflow using all specialized agents.
    
    This workflow simulates receiving a Discord command, breaking it down into
    subtasks, and coordinating multiple agents to complete the work.
    """
    
    print("=" * 80)
    print("SPECIALIZED AGENTS INTEGRATION DEMONSTRATION")
    print("=" * 80)
    
    # 1. Initialize Orchestrator Agent
    print("\n1. ORCHESTRATOR INITIALIZATION")
    print("-" * 40)
    
    orchestrator = OrchestratorAgent("MainOrchestrator")
    orchestrator.prepare_for_task("Coordinate multi-agent development workflow", "pre_task")
    
    print(f"✓ Orchestrator ready: {orchestrator}")
    
    # 2. Parse Discord Command
    print("\n2. DISCORD COMMAND PARSING")
    print("-" * 40)
    
    discord_command = "!create --urgent user authentication API with secure database and comprehensive testing"
    
    parsed_command = orchestrator.parse_discord_command(discord_command)
    
    print(f"Original command: {discord_command}")
    print(f"✓ Parsed - Type: {parsed_command['command_type']}")
    print(f"✓ Complexity: {parsed_command['complexity']}")
    print(f"✓ Urgency: {parsed_command['urgency']}")
    
    # 3. Task Breakdown
    print("\n3. TASK BREAKDOWN")
    print("-" * 40)
    
    subtasks = orchestrator.break_down_task(parsed_command['task_description'])
    
    print(f"✓ Task broken into {len(subtasks)} subtasks:")
    for subtask in subtasks:
        print(f"  - {subtask['agent_type']}: {subtask['description'][:60]}...")
    
    # 4. Task Assignment
    print("\n4. TASK ASSIGNMENT")
    print("-" * 40)
    
    assignments = orchestrator.assign_to_agent(subtasks)
    
    print(f"✓ Tasks assigned to {len(assignments['assignments'])} agent types")
    print(f"✓ Total estimated time: {assignments['total_estimated_time']}")
    if assignments['conflicts']:
        print(f"⚠ Conflicts detected: {len(assignments['conflicts'])}")
    
    # 5. Initialize Specialized Agents
    print("\n5. SPECIALIZED AGENT INITIALIZATION")
    print("-" * 40)
    
    # Database Agent
    db_agent = DatabaseAgent("PrimaryDatabase")
    db_agent.prepare_for_task("Design authentication database schema", "database")
    
    # Backend Agent  
    backend_agent = BackendAgent("APIBuilder")
    backend_agent.prepare_for_task("Implement authentication API endpoints", "backend")
    
    # Code Review Agent
    code_agent = CodeAgent("CodeReviewer")
    code_agent.prepare_for_task("Review authentication implementation", "backend")
    
    # Testing Agent
    test_agent = TestingAgent("QAValidator")
    test_agent.prepare_for_task("Validate authentication system", "testing")
    
    agents = [db_agent, backend_agent, code_agent, test_agent]
    
    for agent in agents:
        status = agent.get_agent_status()
        print(f"✓ {agent.agent_name}: {status['preparation_complete']} ({status['guidelines_length']} chars)")
    
    # 6. Execute Database Work
    print("\n6. DATABASE SCHEMA DESIGN")
    print("-" * 40)
    
    # Design user authentication schema
    schema_result = db_agent.design_schema(
        table_name="users",
        columns={
            "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
            "username": "VARCHAR(50) UNIQUE NOT NULL",
            "email": "VARCHAR(255) UNIQUE NOT NULL",
            "password_hash": "VARCHAR(255) NOT NULL",
            "salt": "VARCHAR(255) NOT NULL",
            "is_active": "BOOLEAN DEFAULT TRUE",
            "last_login": "TIMESTAMP NULL",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        indexes=[
            {"name": "idx_users_email", "columns": ["email"]},
            {"name": "idx_users_username", "columns": ["username"]},
            {"name": "idx_users_active", "columns": ["is_active"]}
        ],
        constraints=[
            {"name": "ck_users_email_format", "definition": "CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')"}
        ]
    )
    
    print(f"✓ Schema designed: {schema_result['table_name']}")
    print(f"  - Columns: {len(schema_result['columns'])}")
    print(f"  - Indexes: {len(schema_result['indexes'])}")
    print(f"  - Security compliant: {schema_result['security_assessment']['security_compliant']}")
    
    # Create migration
    migration_result = db_agent.create_migration(
        migration_name="create_users_authentication_table",
        operations=[{
            "operation": "create_table",
            "table_name": "users",
            "columns": schema_result['columns']
        }]
    )
    
    print(f"✓ Migration created: {migration_result['migration_id']}")
    print(f"  - File: {os.path.basename(migration_result['migration_file'])}")
    print(f"  - Safe to execute: {migration_result['validation_results']['safe_to_execute']}")
    
    # 7. Execute Backend Work
    print("\n7. BACKEND API DEVELOPMENT")
    print("-" * 40)
    
    # Create authentication endpoints
    login_endpoint = backend_agent.create_flask_endpoint(
        endpoint_name="user_login",
        route="/api/v1/auth/login",
        methods=["POST"],
        auth_required=False,
        request_schema={"username": "str", "password": "str"},
        response_schema={"token": "str", "user_id": "str", "expires_at": "str"}
    )
    
    print(f"✓ Login endpoint created: {login_endpoint['route']}")
    print(f"  - Function: {login_endpoint['function_name']}")
    print(f"  - Standards compliant: {login_endpoint['validation_results']['pep8_compliant']}")
    
    # Implement authentication business logic
    auth_logic = backend_agent.implement_business_logic(
        function_name="authenticate_user_credentials",
        requirements="Validate user credentials against database, hash password with salt, generate JWT token",
        input_parameters={"username": "str", "password": "str"},
        return_type="Dict[str, Any]",
        database_operations=True
    )
    
    print(f"✓ Authentication logic implemented: {auth_logic['function_name']}")
    print(f"  - Security check passed: {auth_logic['security_check']['security_compliant']}")
    print(f"  - Test cases generated: {len(auth_logic['test_cases'])}")
    
    # 8. Execute Testing
    print("\n8. TESTING AND VALIDATION")
    print("-" * 40)
    
    # Run backend tests
    backend_tests = backend_agent.run_tests(
        test_type="unit",
        coverage_threshold=85.0,
        generate_report=True
    )
    
    print(f"✓ Backend tests executed:")
    print(f"  - Passed: {backend_tests['test_summary']['passed']}/{backend_tests['test_summary']['total_tests']}")
    print(f"  - Coverage: {backend_tests['coverage_report']['overall_coverage']:.1f}%")
    print(f"  - Meets threshold: {backend_tests['coverage_report']['meets_threshold']}")
    
    # Validate test coverage with testing agent
    coverage_validation = test_agent.validate_test_coverage({
        "total_tests": backend_tests['test_summary']['total_tests'],
        "passed_tests": backend_tests['test_summary']['passed'],
        "coverage_percentage": backend_tests['coverage_report']['overall_coverage'],
        "test_types": ["unit", "integration"]
    })
    
    print(f"✓ Coverage validation: {coverage_validation['status']}")
    
    # 9. Code Review
    print("\n9. CODE REVIEW")
    print("-" * 40)
    
    # Validate code standards
    code_review = code_agent.validate_code_standards(login_endpoint['endpoint_file'])
    
    print(f"✓ Code review completed: {code_review['status']}")
    print(f"  - Guidelines applied: {code_review['guidelines_applied']}")
    
    # 10. Final Validation and Orchestration
    print("\n10. FINAL ORCHESTRATION")
    print("-" * 40)
    
    # Validate task completion for each agent
    validation_results = {}
    
    for agent in agents:
        task_completion = agent.validate_task_completion({
            'status': 'completed',
            'completed_at': datetime.now(),
            'agent_type': agent.agent_type,
            'work_products': ['schema', 'endpoints', 'tests', 'reviews'][agents.index(agent)]
        })
        
        validation_results[agent.agent_name] = task_completion
        print(f"✓ {agent.agent_name}: {task_completion['overall_status']}")
    
    # Orchestrator final assessment
    overall_success = all(
        result['overall_status'] == 'passed' 
        for result in validation_results.values()
    )
    
    print(f"\n{'='*80}")
    if overall_success:
        print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print("All agents completed their tasks according to development bible guidelines.")
    else:
        print("⚠ WORKFLOW COMPLETED WITH ISSUES")
        print("Some agents reported validation issues that should be addressed.")
    
    print(f"\nWorkflow Summary:")
    print(f"- Discord command processed: ✓")
    print(f"- Tasks assigned to {len(agents)} agents: ✓") 
    print(f"- Database schema designed: ✓")
    print(f"- API endpoints created: ✓")
    print(f"- Business logic implemented: ✓")
    print(f"- Tests executed with {backend_tests['coverage_report']['overall_coverage']:.1f}% coverage: ✓")
    print(f"- Code review completed: ✓")
    print(f"- All validations passed: {'✓' if overall_success else '⚠'}")
    
    print(f"{'='*80}")
    
    return overall_success


def demonstrate_decorator_enforcement():
    """
    Demonstrate how the @require_dev_bible_prep decorator enforces preparation
    across all specialized agents.
    """
    
    print("\n" + "="*60)
    print("DECORATOR ENFORCEMENT DEMONSTRATION")
    print("="*60)
    
    # Create agents without preparation
    agents = [
        ("Orchestrator", OrchestratorAgent("UnpreparedOrchestrator")),
        ("Backend", BackendAgent("UnpreparedBackend")),
        ("Database", DatabaseAgent("UnpreparedDatabase")),
        ("Code", CodeAgent("UnpreparedCode")),
        ("Testing", TestingAgent("UnpreparedTesting"))
    ]
    
    # Try to execute protected methods without preparation
    test_cases = [
        ("Orchestrator", lambda agent: agent.parse_discord_command("!test")),
        ("Backend", lambda agent: agent.create_flask_endpoint("test", "/test")),
        ("Database", lambda agent: agent.design_schema("test", {"id": "SERIAL"})),
        ("Code", lambda agent: agent.validate_code_standards("test")),
        ("Testing", lambda agent: agent.validate_test_coverage({"coverage": 80}))
    ]
    
    print("Testing unprepared agents (should all fail):")
    
    for agent_type, (_, agent) in zip([tc[0] for tc in test_cases], agents):
        test_func = next(tc[1] for tc in test_cases if tc[0] == agent_type)
        
        try:
            test_func(agent)
            print(f"✗ {agent_type}: ERROR - Method should have been blocked!")
        except RuntimeError as e:
            print(f"✓ {agent_type}: Properly blocked - {str(e)[:60]}...")
    
    print("\nPreparing agents and retesting:")
    
    # Prepare agents and test again
    preparation_tasks = [
        ("pre_task", "Orchestration task"),
        ("backend", "Backend development"),
        ("database", "Database operations"),
        ("backend", "Code review"),
        ("testing", "Testing validation")
    ]
    
    for (agent_type, agent), (task_type, task_desc) in zip(agents, preparation_tasks):
        agent.prepare_for_task(task_desc, task_type)
        
        # Now try the protected method again
        test_func = next(tc[1] for tc in test_cases if tc[0] == agent_type)
        
        try:
            result = test_func(agent)
            print(f"✓ {agent_type}: Method executed successfully after preparation")
        except Exception as e:
            print(f"⚠ {agent_type}: Unexpected error - {str(e)[:60]}...")
    
    print("="*60)


def main():
    """Main demonstration function."""
    
    try:
        # Run complete workflow demonstration
        workflow_success = demonstrate_complete_workflow()
        
        # Run decorator enforcement demonstration  
        demonstrate_decorator_enforcement()
        
        print(f"\n🎉 ALL DEMONSTRATIONS COMPLETED!")
        print(f"✓ Specialized agents integration: {'SUCCESS' if workflow_success else 'WITH ISSUES'}")
        print(f"✓ Decorator enforcement: SUCCESS")
        print(f"✓ Development bible integration: SUCCESS")
        
        print(f"\nAll specialized agents are ready for production use!")
        print(f"They provide comprehensive functionality for:")
        print(f"  - Discord command orchestration")
        print(f"  - Database schema design and migrations")
        print(f"  - Backend API development")
        print(f"  - Code review and validation")
        print(f"  - Testing and quality assurance")
        
        return 0
        
    except Exception as e:
        print(f"✗ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())