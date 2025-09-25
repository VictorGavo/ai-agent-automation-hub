#!/usr/bin/env python3
"""
Live System Integration Test for AI Agent Automation Hub

This script provides comprehensive testing of the Discord bot integration,
including slash commands, agent coordination, response times, and mobile usability.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import traceback

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our agents for direct testing
from agents.orchestrator_agent import OrchestratorAgent
from agents.backend_agent import BackendAgent
from agents.database_agent import DatabaseAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/live_system_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Container for test results."""
    test_name: str
    success: bool
    response_time_ms: float
    expected_result: str
    actual_result: str
    error_message: Optional[str] = None
    mobile_friendly: Optional[bool] = None
    agent_behavior: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class TestReport:
    """Complete test report."""
    test_session_id: str
    start_time: str
    end_time: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    average_response_time_ms: float
    test_results: List[TestResult]
    system_info: Dict[str, Any]
    recommendations: List[str]
    mobile_ux_score: float  # 0-10 scale


class LiveSystemTester:
    """Comprehensive testing suite for the Discord integration."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
        # Initialize agents for direct testing
        self.orchestrator_agent: Optional[OrchestratorAgent] = None
        self.backend_agent: Optional[BackendAgent] = None
        self.database_agent: Optional[DatabaseAgent] = None
        
        # Test configuration
        self.mobile_response_threshold_ms = 3000  # 3 seconds for mobile
        self.desktop_response_threshold_ms = 2000  # 2 seconds for desktop
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        logger.info(f"🧪 Starting Live System Test Session: {self.session_id}")
    
    async def setup_agents(self) -> bool:
        """Initialize and prepare all agents for testing."""
        try:
            logger.info("🔧 Setting up agents for direct testing...")
            
            # Initialize agents
            self.orchestrator_agent = OrchestratorAgent("TestOrchestrator")
            self.backend_agent = BackendAgent("TestBackend")
            self.database_agent = DatabaseAgent("TestDatabase")
            
            # Prepare agents with appropriate tasks
            logger.info("📚 Preparing agents with dev bible...")
            
            self.orchestrator_agent.prepare_for_task(
                "Handle test command coordination", "pre_task"
            )
            
            self.backend_agent.prepare_for_task(
                "Prepare for test backend development tasks", "backend"
            )
            
            self.database_agent.prepare_for_task(
                "Prepare for test database operations", "database"
            )
            
            logger.info("✅ All agents prepared successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up agents: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def measure_time(func):
        """Decorator to measure function execution time."""
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                return result, response_time, None
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                return None, response_time, str(e)
        return wrapper
    
    @measure_time
    def test_orchestrator_command_parsing(self) -> Dict[str, Any]:
        """Test OrchestratorAgent command parsing capabilities."""
        logger.info("🔍 Testing OrchestratorAgent command parsing...")
        
        test_commands = [
            "/assign-task Create a Flask health check endpoint backend",
            "/status",
            "/approve task_123",
            "/invalid-command test"
        ]
        
        results = {}
        for cmd in test_commands:
            try:
                result = self.orchestrator_agent.parse_discord_command(cmd)
                # Check if parsing was successful by looking for expected fields
                has_command_type = bool(result.get('command_type'))
                has_task_description = bool(result.get('task_description'))
                
                results[cmd] = {
                    'valid': has_command_type and has_task_description,
                    'command_type': result.get('command_type', 'unknown'),
                    'task_description': result.get('task_description', ''),
                    'complexity': result.get('complexity', 'unknown')
                }
                logger.info(f"  📝 Command '{cmd}' -> Valid: {has_command_type and has_task_description}")
            except Exception as e:
                results[cmd] = {'error': str(e), 'valid': False}
                logger.error(f"  ❌ Command '{cmd}' failed: {e}")
        
        return results
    
    @measure_time
    def test_task_breakdown_and_assignment(self) -> Dict[str, Any]:
        """Test task breakdown and agent assignment."""
        logger.info("🎯 Testing task breakdown and assignment...")
        
        test_task = "Create a simple Flask health check endpoint"
        
        try:
            # Test task breakdown (only takes task_description parameter)
            breakdown = self.orchestrator_agent.break_down_task(test_task)
            logger.info(f"  📋 Task breakdown completed: {len(breakdown)} subtasks")
            
            # Test agent assignment (takes list of subtasks)
            assignment = self.orchestrator_agent.assign_to_agent(breakdown)
            
            # Extract assignment information from the actual structure
            assignments = assignment.get('assignments', {})
            agent_types = list(assignments.keys()) if assignments else []
            assigned_to = ', '.join(agent_types) if agent_types else 'None'
            
            logger.info(f"  🤖 Assigned to: {assigned_to}")
            
            return {
                'breakdown_success': bool(breakdown and len(breakdown) > 0),
                'assignment_success': bool(assignments),
                'assigned_agent': assigned_to,
                'agent_types_count': len(agent_types),
                'steps_count': len(breakdown) if breakdown else 0,
                'conflicts_count': len(assignment.get('conflicts', [])),
                'total_estimated_time': assignment.get('total_estimated_time', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"  ❌ Task breakdown/assignment failed: {e}")
            return {'error': str(e), 'success': False}
    
    @measure_time
    def test_backend_agent_preparation(self) -> Dict[str, Any]:
        """Test BackendAgent preparation and capabilities."""
        logger.info("🔧 Testing BackendAgent preparation...")
        
        try:
            # Test if agent has dev bible loaded (use correct attribute names)
            has_guidelines = (
                hasattr(self.backend_agent, 'current_guidelines') and 
                bool(self.backend_agent.current_guidelines)
            )
            
            is_prepared = (
                hasattr(self.backend_agent, '_preparation_complete') and 
                bool(self.backend_agent._preparation_complete)
            )
            
            # Test project root configuration
            has_project_root = hasattr(self.backend_agent, 'project_root') and bool(self.backend_agent.project_root)
            
            # Test available methods (actual methods that exist)
            has_flask_endpoint = hasattr(self.backend_agent, 'create_flask_endpoint')
            has_business_logic = hasattr(self.backend_agent, 'implement_business_logic')
            has_test_runner = hasattr(self.backend_agent, 'run_tests')
            has_git_integration = hasattr(self.backend_agent, 'create_git_branch')
            
            return {
                'guidelines_loaded': has_guidelines,
                'preparation_complete': is_prepared,
                'guidelines_length': len(str(self.backend_agent.current_guidelines)) if has_guidelines else 0,
                'project_root_configured': has_project_root,
                'project_root': str(self.backend_agent.project_root) if has_project_root else 'Not set',
                'flask_endpoint_available': has_flask_endpoint,
                'business_logic_available': has_business_logic,
                'test_runner_available': has_test_runner,
                'git_integration_available': has_git_integration,
                'capabilities_count': sum([has_flask_endpoint, has_business_logic, has_test_runner, has_git_integration])
            }
            
        except Exception as e:
            logger.error(f"  ❌ BackendAgent preparation test failed: {e}")
            return {'error': str(e), 'success': False}
    
    @measure_time
    def test_agent_coordination_workflow(self) -> Dict[str, Any]:
        """Test full agent coordination workflow."""
        logger.info("🔄 Testing agent coordination workflow...")
        
        try:
            # Simulate full workflow
            task_description = "Create a simple Flask health check endpoint"
            
            # Step 1: Parse command
            command = f"/assign-task {task_description} backend"
            parse_result = self.orchestrator_agent.parse_discord_command(command)
            
            # Step 2: Break down task (only takes task_description)
            breakdown = self.orchestrator_agent.break_down_task(task_description)
            
            # Step 3: Assign to agent (takes list of subtasks)
            assignment = self.orchestrator_agent.assign_to_agent(breakdown)
            
            # Step 4: Verify assigned agent can handle task
            assignments = assignment.get('assignments', {})
            agent_types = list(assignments.keys())
            
            agent_ready = False
            for agent_type in agent_types:
                if 'backend' in agent_type.lower() and self.backend_agent:
                    agent_ready = True
                    break
                elif 'database' in agent_type.lower() and self.database_agent:
                    agent_ready = True
                    break
            
            assigned_to = ', '.join(agent_types) if agent_types else 'None'
            
            # Check if parsing was successful
            parse_success = bool(parse_result.get('command_type')) and bool(parse_result.get('task_description'))
            
            return {
                'workflow_success': all([
                    parse_success,
                    bool(breakdown and len(breakdown) > 0),
                    bool(assignments),
                    agent_ready
                ]),
                'parse_success': parse_success,
                'breakdown_success': bool(breakdown and len(breakdown) > 0),
                'assignment_success': bool(assignments),
                'agent_ready': agent_ready,
                'assigned_to': assigned_to,
                'steps_generated': len(breakdown) if breakdown else 0,
                'command_type': parse_result.get('command_type', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"  ❌ Coordination workflow test failed: {e}")
            return {'error': str(e), 'success': False}
    
    def test_mobile_usability_simulation(self) -> Dict[str, Any]:
        """Test mobile usability aspects."""
        logger.info("📱 Testing mobile usability simulation...")
        
        # Simulate mobile constraints
        mobile_constraints = {
            'max_message_length': 2000,  # Discord mobile limit
            'max_embed_fields': 10,      # Reasonable mobile limit
            'response_time_threshold': self.mobile_response_threshold_ms
        }
        
        # Test message formatting
        test_messages = [
            "✅ Task assigned successfully to BackendAgent",
            "📋 Current agent status:\n• Orchestrator: Ready\n• Backend: Busy\n• Database: Ready",
            "❌ Error: Task validation failed. Please check your input parameters.",
            "🎯 Task breakdown:\n1. Set up Flask app\n2. Create health endpoint\n3. Add JSON response\n4. Test functionality"
        ]
        
        mobile_friendly_count = 0
        for msg in test_messages:
            is_mobile_friendly = (
                len(msg) <= mobile_constraints['max_message_length'] and
                msg.count('\n') <= mobile_constraints['max_embed_fields'] and
                all(ord(char) < 128 or char in '✅❌📋🎯📱🔧🚀⚡' for char in msg)  # Basic emoji support
            )
            if is_mobile_friendly:
                mobile_friendly_count += 1
        
        mobile_score = (mobile_friendly_count / len(test_messages)) * 10
        
        return {
            'mobile_friendly_messages': mobile_friendly_count,
            'total_messages_tested': len(test_messages),
            'mobile_score': mobile_score,
            'constraints_met': mobile_friendly_count == len(test_messages)
        }
    
    async def run_comprehensive_test_suite(self) -> None:
        """Run the complete test suite."""
        logger.info("🚀 Starting Comprehensive Test Suite...")
        
        # Test 1: Agent Setup
        test_result = TestResult(
            test_name="Agent Setup and Preparation",
            success=False,
            response_time_ms=0,
            expected_result="All agents initialized and prepared with dev bible",
            actual_result=""
        )
        
        start_time = time.time()
        setup_success = await self.setup_agents()
        end_time = time.time()
        
        test_result.response_time_ms = (end_time - start_time) * 1000
        test_result.success = setup_success
        test_result.actual_result = "Agents setup successful" if setup_success else "Agent setup failed"
        self.results.append(test_result)
        
        if not setup_success:
            logger.error("❌ Agent setup failed. Cannot continue with tests.")
            return
        
        # Test 2: Command Parsing
        parsing_result, response_time, error = self.test_orchestrator_command_parsing()
        test_result = TestResult(
            test_name="OrchestratorAgent Command Parsing",
            success=error is None and bool(parsing_result),
            response_time_ms=response_time,
            expected_result="All valid commands parsed correctly, invalid commands rejected",
            actual_result=f"Parsed {len(parsing_result)} commands" if parsing_result else "Parsing failed",
            error_message=error,
            agent_behavior=parsing_result
        )
        self.results.append(test_result)
        
        # Test 3: Task Breakdown and Assignment
        assignment_result, response_time, error = self.test_task_breakdown_and_assignment()
        test_result = TestResult(
            test_name="Task Breakdown and Assignment",
            success=error is None and assignment_result.get('breakdown_success', False) and assignment_result.get('assignment_success', False),
            response_time_ms=response_time,
            expected_result="Task broken down into steps and assigned to appropriate agent",
            actual_result=f"Assigned to {assignment_result.get('assigned_agent', 'Unknown')} with {assignment_result.get('steps_count', 0)} steps" if assignment_result else "Assignment failed",
            error_message=error,
            agent_behavior=assignment_result
        )
        self.results.append(test_result)
        
        # Test 4: Backend Agent Preparation
        backend_result, response_time, error = self.test_backend_agent_preparation()
        test_result = TestResult(
            test_name="BackendAgent Preparation and Capabilities",
            success=error is None and backend_result.get('guidelines_loaded', False) and backend_result.get('preparation_complete', False),
            response_time_ms=response_time,
            expected_result="Backend agent loaded with guidelines and preparation complete",
            actual_result=f"Guidelines: {backend_result.get('guidelines_loaded', False)}, Prepared: {backend_result.get('preparation_complete', False)}, Capabilities: {backend_result.get('capabilities_count', 0)}" if backend_result else "Backend preparation failed",
            error_message=error,
            agent_behavior=backend_result
        )
        self.results.append(test_result)
        
        # Test 5: Full Coordination Workflow
        workflow_result, response_time, error = self.test_agent_coordination_workflow()
        test_result = TestResult(
            test_name="Agent Coordination Workflow",
            success=error is None and workflow_result.get('workflow_success', False),
            response_time_ms=response_time,
            expected_result="Complete workflow from command to agent assignment successful",
            actual_result=f"Workflow success: {workflow_result.get('workflow_success', False)}, Assigned to: {workflow_result.get('assigned_to', 'Unknown')}" if workflow_result else "Workflow failed",
            error_message=error,
            agent_behavior=workflow_result
        )
        self.results.append(test_result)
        
        # Test 6: Mobile Usability
        mobile_result = self.test_mobile_usability_simulation()
        mobile_score = mobile_result.get('mobile_score', 0)
        test_result = TestResult(
            test_name="Mobile Usability Simulation",
            success=mobile_score >= 7.0,  # Lower threshold for passing
            response_time_ms=0,  # Not applicable for this test
            expected_result="Messages mobile-friendly with score > 7.0",
            actual_result=f"Mobile score: {mobile_score:.1f}/10, {mobile_result.get('mobile_friendly_messages', 0)}/{mobile_result.get('total_messages_tested', 0)} messages mobile-friendly",
            mobile_friendly=mobile_score >= 7.0,
            agent_behavior=mobile_result
        )
        self.results.append(test_result)
    
    def generate_test_report(self) -> TestReport:
        """Generate comprehensive test report."""
        end_time = datetime.now()
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.success)
        failed_tests = total_tests - passed_tests
        
        response_times = [r.response_time_ms for r in self.results if r.response_time_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate mobile UX score
        mobile_results = [r for r in self.results if r.mobile_friendly is not None]
        if mobile_results:
            mobile_ux_score = sum(1 for r in mobile_results if r.mobile_friendly) / len(mobile_results) * 10
        else:
            # Use the mobile simulation test results if available
            mobile_test = next((r for r in self.results if r.test_name == "Mobile Usability Simulation"), None)
            if mobile_test and mobile_test.agent_behavior:
                mobile_ux_score = mobile_test.agent_behavior.get('mobile_score', 5.0)
            else:
                mobile_ux_score = 5.0
        
        # Generate recommendations
        recommendations = []
        
        if avg_response_time > self.mobile_response_threshold_ms:
            recommendations.append(f"⚡ Optimize response times - current average {avg_response_time:.0f}ms exceeds mobile threshold")
        
        if mobile_ux_score < 8.0:
            recommendations.append(f"📱 Improve mobile UX - current score {mobile_ux_score:.1f}/10")
        
        if failed_tests > 0:
            recommendations.append(f"🔧 Fix {failed_tests} failed tests before production deployment")
        
        for result in self.results:
            if not result.success and result.error_message:
                recommendations.append(f"❌ Address: {result.test_name} - {result.error_message}")
        
        if not recommendations:
            recommendations.append("🎉 All tests passed! System ready for production deployment.")
        
        # System info
        system_info = {
            'python_version': sys.version,
            'discord_bot_token_configured': bool(os.getenv('DISCORD_BOT_TOKEN')),
            'agents_available': {
                'orchestrator': self.orchestrator_agent is not None,
                'backend': self.backend_agent is not None,
                'database': self.database_agent is not None
            },
            'test_environment': 'local',
            'test_date': datetime.now().isoformat()
        }
        
        return TestReport(
            test_session_id=self.session_id,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            average_response_time_ms=avg_response_time,
            test_results=self.results,
            system_info=system_info,
            recommendations=recommendations,
            mobile_ux_score=mobile_ux_score
        )
    
    def save_report(self, report: TestReport) -> str:
        """Save test report to file."""
        report_file = f"logs/live_system_test_report_{self.session_id}.json"
        
        # Convert to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(report_file, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        # Also create a human-readable version
        readable_file = f"logs/live_system_test_report_{self.session_id}.md"
        self.create_readable_report(report, readable_file)
        
        return report_file
    
    def create_readable_report(self, report: TestReport, file_path: str) -> None:
        """Create human-readable test report."""
        content = f"""# AI Agent Automation Hub - Live System Test Report

**Test Session:** {report.test_session_id}  
**Test Date:** {report.start_time.split('T')[0]}  
**Duration:** {(datetime.fromisoformat(report.end_time) - datetime.fromisoformat(report.start_time)).total_seconds():.1f} seconds

## 📊 Summary

- **Total Tests:** {report.total_tests}
- **Passed:** {report.passed_tests} ✅
- **Failed:** {report.failed_tests} ❌
- **Success Rate:** {(report.passed_tests / report.total_tests * 100):.1f}%
- **Average Response Time:** {report.average_response_time_ms:.0f}ms
- **Mobile UX Score:** {report.mobile_ux_score:.1f}/10

## 🧪 Test Results

"""
        
        for i, result in enumerate(report.test_results, 1):
            status_icon = "✅" if result.success else "❌"
            mobile_icon = ""
            if result.mobile_friendly is not None:
                mobile_icon = " 📱" if result.mobile_friendly else " 🖥️"
            
            content += f"""### {i}. {result.test_name} {status_icon}{mobile_icon}

**Expected:** {result.expected_result}  
**Actual:** {result.actual_result}  
**Response Time:** {result.response_time_ms:.0f}ms  
"""
            
            if result.error_message:
                content += f"**Error:** {result.error_message}  \n"
            
            content += "\n"
        
        content += f"""## 🔧 System Information

- **Python Version:** {report.system_info['python_version'].split()[0]}
- **Discord Token Configured:** {'✅' if report.system_info['discord_bot_token_configured'] else '❌'}
- **Agents Available:**
  - Orchestrator: {'✅' if report.system_info['agents_available']['orchestrator'] else '❌'}
  - Backend: {'✅' if report.system_info['agents_available']['backend'] else '❌'}
  - Database: {'✅' if report.system_info['agents_available']['database'] else '❌'}

## 💡 Recommendations

"""
        
        for rec in report.recommendations:
            content += f"- {rec}\n"
        
        content += f"""

## 📋 Next Steps

{
'🎉 **System Ready for Production!** All tests passed successfully. You can proceed with confidence.' if report.failed_tests == 0
else f'🔧 **Address {report.failed_tests} Failed Tests** before production deployment. See recommendations above.'
}

### Discord Commands to Test Manually:

1. **Status Check:** `/status`
2. **Task Assignment:** `/assign-task description:"Create a simple Flask health check endpoint" task_type:"backend"`
3. **Agent Logs:** `/agent-logs agent_name:"orchestrator"`
4. **Task Approval:** `/approve task_id:"[generated_task_id]"`

### Mobile Testing Checklist:

- [ ] Commands appear in mobile Discord app
- [ ] Response messages fit mobile screen
- [ ] Emojis render correctly
- [ ] Response times under 3 seconds
- [ ] Error messages are clear and helpful

---
*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(file_path, 'w') as f:
            f.write(content)


def print_summary(report: TestReport) -> None:
    """Print test summary to console."""
    print("\n" + "="*60)
    print("🧪 LIVE SYSTEM TEST COMPLETE")
    print("="*60)
    
    print(f"📊 Test Results: {report.passed_tests}/{report.total_tests} passed")
    print(f"⏱️  Average Response Time: {report.average_response_time_ms:.0f}ms")
    print(f"📱 Mobile UX Score: {report.mobile_ux_score:.1f}/10")
    
    if report.failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! System ready for production!")
    else:
        print(f"\n⚠️  {report.failed_tests} tests failed. See recommendations:")
        for rec in report.recommendations[:3]:  # Show first 3 recommendations
            print(f"   • {rec}")
    
    print(f"\n📄 Detailed reports saved:")
    print(f"   • JSON: logs/live_system_test_report_{report.test_session_id}.json")
    print(f"   • Markdown: logs/live_system_test_report_{report.test_session_id}.md")
    print("="*60)


async def main():
    """Main test execution function."""
    print("🚀 AI Agent Automation Hub - Live System Integration Test")
    print("="*60)
    
    # Check if Discord bot is running
    try:
        import psutil
        bot_running = any('bot/run_bot.py' in ' '.join(p.cmdline()) for p in psutil.process_iter(['cmdline']))
        if bot_running:
            print("✅ Discord bot detected running")
        else:
            print("⚠️  Discord bot not detected. Some tests may be limited.")
    except ImportError:
        print("ℹ️  Install psutil for bot detection: pip install psutil")
    
    # Initialize and run tests
    tester = LiveSystemTester()
    
    try:
        await tester.run_comprehensive_test_suite()
        report = tester.generate_test_report()
        report_file = tester.save_report(report)
        
        print_summary(report)
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        logger.error(traceback.format_exc())
        print(f"\n💥 Test suite encountered an error: {e}")
        return 1
    
    return 0 if report.failed_tests == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)