#!/usr/bin/env python3
"""
BaseAgent Integration Example

This example demonstrates how to integrate the new BaseAgent class
with existing agent functionality and how specialized agents can
inherit from BaseAgent to gain development bible integration.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, CodeAgent, TestingAgent, require_dev_bible_prep


class DatabaseAgent(BaseAgent):
    """
    Example of creating a specialized DatabaseAgent that inherits from BaseAgent.
    
    This demonstrates how to extend BaseAgent for specific domain expertise
    while maintaining all the development bible integration functionality.
    """
    
    def __init__(self, agent_name: str, dev_bible_path: str = None):
        """Initialize DatabaseAgent with 'database' type."""
        super().__init__(agent_name, "database", dev_bible_path)
        self.connection_pool = None
        print(f"DatabaseAgent {agent_name} initialized with database-specific capabilities")
    
    @require_dev_bible_prep
    def validate_schema_changes(self, schema_changes: dict) -> dict:
        """
        Validate database schema changes against security and architecture guidelines.
        
        Args:
            schema_changes (dict): Proposed schema modifications
            
        Returns:
            dict: Validation results including security compliance
        """
        print(f"Validating schema changes for {self.agent_name} using loaded guidelines...")
        
        # Example validation logic that would use the loaded guidelines
        validation_result = {
            'agent_name': self.agent_name,
            'validation_type': 'schema_security',
            'timestamp': datetime.now(),
            'guidelines_applied': bool(self.current_guidelines),
            'security_compliant': True,
            'changes_validated': len(schema_changes) if schema_changes else 0,
            'recommendations': [
                "Schema changes follow security guidelines from dev_bible",
                "Architecture patterns maintained as specified in guidelines"
            ]
        }
        
        return validation_result
    
    @require_dev_bible_prep 
    def execute_migration(self, migration_script: str) -> dict:
        """
        Execute database migration following guidelines.
        
        Args:
            migration_script (str): SQL migration script
            
        Returns:
            dict: Migration execution results
        """
        print(f"Executing migration for {self.agent_name} with guideline compliance...")
        
        # This would contain actual migration logic
        return {
            'agent_name': self.agent_name,
            'migration_status': 'completed',
            'guidelines_followed': True,
            'timestamp': datetime.now()
        }


class DocumentationAgent(BaseAgent):
    """
    Example DocumentationAgent showing how to integrate with BaseAgent
    for documentation-specific tasks.
    """
    
    def __init__(self, agent_name: str, dev_bible_path: str = None):
        """Initialize DocumentationAgent with 'documentation' type."""
        super().__init__(agent_name, "documentation", dev_bible_path)
        print(f"DocumentationAgent {agent_name} initialized")
    
    @require_dev_bible_prep
    def generate_api_docs(self, api_specification: dict) -> dict:
        """
        Generate API documentation following communication guidelines.
        
        Args:
            api_specification (dict): API specification details
            
        Returns:
            dict: Generated documentation metadata
        """
        print(f"Generating API documentation for {self.agent_name} using communication guidelines...")
        
        return {
            'agent_name': self.agent_name,
            'documentation_type': 'api',
            'guidelines_applied': bool(self.current_guidelines),
            'communication_standards_met': True,
            'timestamp': datetime.now()
        }


def demonstrate_agent_workflow():
    """
    Demonstrate a complete workflow using BaseAgent and specialized agents.
    """
    print("="*80)
    print("BASEAGENT INTEGRATION DEMONSTRATION")
    print("="*80)
    
    # 1. Create specialized agents
    print("\n1. CREATING SPECIALIZED AGENTS")
    print("-" * 40)
    
    # Database agent for schema work
    db_agent = DatabaseAgent("PrimaryDBAgent")
    
    # Code agent for backend work  
    code_agent = CodeAgent("BackendCodeAgent")
    
    # Documentation agent for docs
    doc_agent = DocumentationAgent("APIDocAgent")
    
    # Testing agent for validation
    test_agent = TestingAgent("QATestAgent")
    
    print(f"✓ Created {len([db_agent, code_agent, doc_agent, test_agent])} specialized agents")
    
    # 2. Demonstrate preparation workflow
    print("\n2. AGENT PREPARATION WORKFLOW")
    print("-" * 40)
    
    # Each agent prepares for their specific task type
    agents_and_tasks = [
        (db_agent, "database schema migration", "database"),
        (code_agent, "backend API development", "backend"), 
        (doc_agent, "API documentation generation", "documentation"),
        (test_agent, "integration testing suite", "testing")
    ]
    
    for agent, task_desc, task_type in agents_and_tasks:
        try:
            agent.prepare_for_task(task_desc, task_type)
            status = agent.get_agent_status()
            print(f"✓ {agent.agent_name}: {status['guidelines_length']} chars loaded for {task_type}")
        except Exception as e:
            print(f"✗ {agent.agent_name} preparation failed: {e}")
    
    # 3. Demonstrate task execution with guidelines
    print("\n3. TASK EXECUTION WITH GUIDELINES")
    print("-" * 40)
    
    # Database agent performs schema validation
    try:
        schema_result = db_agent.validate_schema_changes({
            'add_table': 'user_sessions',
            'add_column': 'encrypted_data'
        })
        print(f"✓ Database validation: {schema_result['security_compliant']}")
    except Exception as e:
        print(f"✗ Database task failed: {e}")
    
    # Code agent validates code standards
    try:
        code_result = code_agent.validate_code_standards("""
def secure_api_endpoint():
    # Implementation following coding standards
    pass
        """)
        print(f"✓ Code validation: {code_result['status']}")
    except Exception as e:
        print(f"✗ Code task failed: {e}")
    
    # Documentation agent generates docs
    try:
        doc_result = doc_agent.generate_api_docs({
            'endpoint': '/api/v1/users',
            'methods': ['GET', 'POST']
        })
        print(f"✓ Documentation: {doc_result['communication_standards_met']}")
    except Exception as e:
        print(f"✗ Documentation task failed: {e}")
    
    # Testing agent validates coverage
    try:
        test_result = test_agent.validate_test_coverage({
            'total_tests': 150,
            'passing': 148,
            'coverage': 95.2
        })
        print(f"✓ Test validation: {test_result['status']}")
    except Exception as e:
        print(f"✗ Testing task failed: {e}")
    
    # 4. Demonstrate validation and compliance
    print("\n4. TASK COMPLETION VALIDATION")
    print("-" * 40)
    
    for agent in [db_agent, code_agent, doc_agent, test_agent]:
        try:
            validation = agent.validate_task_completion({
                'status': 'completed',
                'completed_at': datetime.now(),
                'agent_type': agent.agent_type
            })
            print(f"✓ {agent.agent_name}: {validation['overall_status']} "
                  f"({len(validation['compliance_checks'])} checks)")
        except Exception as e:
            print(f"✗ {agent.agent_name} validation failed: {e}")
    
    # 5. Show guidelines context usage
    print("\n5. GUIDELINES CONTEXT FOR LLM INTEGRATION")
    print("-" * 40)
    
    # Example of how to get guidelines for LLM context
    sample_agent = code_agent
    guidelines_context = sample_agent.get_guidelines_context()
    
    print(f"✓ Guidelines context ready for LLM prompts:")
    print(f"  - Agent: {sample_agent.agent_name}")
    print(f"  - Context length: {len(guidelines_context)} characters")
    print(f"  - Task type: {sample_agent.current_task_type}")
    print(f"  - Includes formatting: {'DEVELOPMENT GUIDELINES CONTEXT' in guidelines_context}")
    
    # 6. Demonstrate error handling
    print("\n6. ERROR HANDLING DEMONSTRATION")
    print("-" * 40)
    
    try:
        # Create unprepared agent and try to execute task
        unprepared_agent = BaseAgent("UnpreparedAgent", "general")
        unprepared_agent.validate_task_completion({'status': 'completed'})
    except RuntimeError as e:
        print(f"✓ Proper error handling for unprepared agent: {str(e)[:60]}...")
    
    try:
        # Try invalid task type
        invalid_agent = BaseAgent("InvalidAgent", "general")
        invalid_agent.prepare_for_task("Test", "invalid_task_type")
    except ValueError as e:
        print(f"✓ Proper error handling for invalid task type: {str(e)[:60]}...")
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("All agents properly integrated with development bible guidelines!")
    print("="*80)


def show_decorator_protection():
    """
    Demonstrate how the @require_dev_bible_prep decorator protects methods.
    """
    print("\n" + "="*60)
    print("DECORATOR PROTECTION DEMONSTRATION")
    print("="*60)
    
    # Create an agent but don't prepare it
    agent = DatabaseAgent("ProtectionTestAgent")
    
    print(f"Agent created: {agent}")
    print(f"Preparation status: {agent.get_agent_status()['preparation_complete']}")
    
    # Try to execute protected method without preparation
    print("\nAttempting to execute protected method without preparation...")
    
    try:
        agent.validate_schema_changes({'test': 'change'})
        print("✗ ERROR: Method should have been blocked!")
    except RuntimeError as e:
        print(f"✓ Method properly blocked: {str(e)[:80]}...")
    
    # Now prepare and try again
    print("\nPreparing agent and retrying...")
    agent.prepare_for_task("Schema validation task", "database")
    
    try:
        result = agent.validate_schema_changes({'test': 'change'})
        print(f"✓ Method executed successfully after preparation: {result['validation_type']}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("="*60)


def main():
    """Main demonstration function."""
    try:
        demonstrate_agent_workflow()
        show_decorator_protection()
        
        print(f"\n🎉 BaseAgent integration demonstration completed successfully!")
        print(f"All agents now have development bible integration and validation!")
        
        return 0
        
    except Exception as e:
        print(f"✗ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())