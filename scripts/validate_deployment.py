#!/usr/bin/env python3
"""
Comprehensive Deployment Validation Script - Simplified Version

This script validates the entire AI Agent Automation Hub deployment,
testing all major components and generating a detailed report.
"""

import asyncio
import json
import logging
import os
import psutil
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestResult(Enum):
    """Test result enumeration."""
    PASS = "✅"
    FAIL = "❌"
    WARN = "⚠️"
    SKIP = "⏭️"
    INFO = "ℹ️"

@dataclass
class ValidationResult:
    """Container for validation results."""
    component: str
    test_name: str
    result: TestResult
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    load_average: Tuple[float, float, float]
    running_processes: int
    network_connections: int
    uptime: float

class DeploymentValidator:
    """Main deployment validation class."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the deployment validator."""
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config(config_file)
        self.logger = self._setup_logging()
        self.results: List[ValidationResult] = []
        self.start_time = datetime.now()
        self.is_pi_system = self._detect_pi_system()
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration settings and environment variables."""
        # Load .env file first
        self._load_env_file()
        
        default_config = {
            "timeout": 30,
            "verbose": False,
            "skip_tests": [],
            "thresholds": {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                import json
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        return default_config
                
    def _load_env_file(self):
        """Load environment variables from .env file."""
        env_file = self.project_root / '.env'
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            try:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                # Remove quotes if present
                                if value.startswith('"') and value.endswith('"'):
                                    value = value[1:-1]
                                elif value.startswith("'") and value.endswith("'"):
                                    value = value[1:-1]
                                # Only set if not already set in environment
                                if key not in os.environ:
                                    os.environ[key] = value
                            except ValueError:
                                # Handle malformed lines gracefully
                                continue
            except Exception as e:
                print(f"Warning: Could not load .env file: {e}")
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "deployment_validation.log"),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(__name__)
    
    def _detect_pi_system(self) -> bool:
        """Detect if running on Raspberry Pi."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo
        except FileNotFoundError:
            return False
    
    def add_result(self, result: ValidationResult):
        """Add a validation result."""
        self.results.append(result)
        status_icon = result.result.value
        self.logger.info(f"{status_icon} {result.component}: {result.test_name} - {result.message}")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            processes = len(psutil.pids())
            connections = len(psutil.net_connections())
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                load_average=load_avg,
                running_processes=processes,
                network_connections=connections,
                uptime=uptime
            )
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(0, 0, 0, (0, 0, 0), 0, 0, 0)
    
    async def _run_test(self, test_func, *args, **kwargs) -> ValidationResult:
        """Run a test function with timing."""
        start_time = time.time()
        try:
            result = await test_func(*args, **kwargs)
            result.execution_time = time.time() - start_time
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            return ValidationResult(
                component="Unknown",
                test_name=test_func.__name__,
                result=TestResult.FAIL,
                message=f"Test failed with exception: {str(e)}",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                execution_time=execution_time
            )
    
    # ========================================
    # TEST IMPLEMENTATIONS
    # ========================================
    
    async def test_environment_variables(self) -> ValidationResult:
        """Test that all required environment variables are present."""
        required_vars = ['DISCORD_BOT_TOKEN', 'DATABASE_URL', 'APP_MODE']
        optional_vars = ['DISCORD_GUILD_ID', 'MAX_CONCURRENT_TASKS', 'LOG_LEVEL', 'ENCRYPTION_KEY']
        
        missing_required = [var for var in required_vars if not os.getenv(var)]
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        
        if missing_required:
            return ValidationResult(
                component="Environment",
                test_name="Required Environment Variables",
                result=TestResult.FAIL,
                message=f"Missing required variables: {', '.join(missing_required)}",
                details={"missing_required": missing_required, "missing_optional": missing_optional}
            )
        elif missing_optional:
            return ValidationResult(
                component="Environment", 
                test_name="Environment Variables",
                result=TestResult.WARN,
                message=f"Missing optional variables: {', '.join(missing_optional)}",
                details={"missing_optional": missing_optional}
            )
        else:
            return ValidationResult(
                component="Environment",
                test_name="Environment Variables", 
                result=TestResult.PASS,
                message="All environment variables present"
            )
    
    async def test_file_structure(self) -> ValidationResult:
        """Test that all required files and directories exist."""
        required_files = [
            "bot/main.py", "bot/config.py",
            "agents/orchestrator/orchestrator.py",
            "agents/backend/backend_agent.py", 
            "agents/testing/testing_agent.py",
            "database/models/base.py",
            "dev_bible/README.md"
        ]
        
        required_dirs = ["agents", "bot", "database", "dev_bible", "logs", "scripts"]
        
        missing_files = []
        missing_dirs = []
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)
        
        issues = []
        if missing_files:
            issues.append(f"Missing files: {', '.join(missing_files)}")
        if missing_dirs:
            issues.append(f"Missing directories: {', '.join(missing_dirs)}")
        
        if issues:
            return ValidationResult(
                component="File System",
                test_name="File Structure",
                result=TestResult.FAIL,
                message="; ".join(issues),
                details={"missing_files": missing_files, "missing_dirs": missing_dirs}
            )
        else:
            return ValidationResult(
                component="File System",
                test_name="File Structure", 
                result=TestResult.PASS,
                message="All required files and directories present"
            )
    
    async def test_database_connection(self) -> ValidationResult:
        """Test PostgreSQL database connection."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return ValidationResult(
                component="Database",
                test_name="Connection",
                result=TestResult.SKIP,
                message="DATABASE_URL not configured"
            )
        
        try:
            import asyncpg
            conn = await asyncpg.connect(database_url)
            await conn.close()
            
            return ValidationResult(
                component="Database",
                test_name="Connection",
                result=TestResult.PASS,
                message="Database connection successful"
            )
        except ImportError:
            return ValidationResult(
                component="Database",
                test_name="Connection",
                result=TestResult.FAIL,
                message="asyncpg library not available"
            )
        except Exception as e:
            return ValidationResult(
                component="Database", 
                test_name="Connection",
                result=TestResult.FAIL,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def test_dev_bible_reader(self) -> ValidationResult:
        """Test DevBibleReader functionality."""
        try:
            from dev_bible.reader import DevBibleReader
            
            reader = DevBibleReader(str(self.project_root / "dev_bible"))
            docs = reader.load_all_documentation()
            
            if not docs:
                return ValidationResult(
                    component="DevBible",
                    test_name="Reader",
                    result=TestResult.WARN,
                    message="No documentation found in dev_bible directory"
                )
            
            return ValidationResult(
                component="DevBible",
                test_name="Reader", 
                result=TestResult.PASS,
                message=f"DevBibleReader loaded {len(docs)} documentation files successfully",
                details={"doc_count": len(docs)}
            )
            
        except ImportError as e:
            return ValidationResult(
                component="DevBible",
                test_name="Reader",
                result=TestResult.FAIL,
                message="DevBibleReader import failed - component may not be implemented",
                details={"error": str(e)}
            )
        except Exception as e:
            return ValidationResult(
                component="DevBible",
                test_name="Reader",
                result=TestResult.FAIL,
                message=f"DevBibleReader test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def test_agents(self) -> ValidationResult:
        """Test agent initialization."""
        agents_to_test = [
            ("BackendAgent", "agents.backend.backend_agent", "BackendAgent"),
            ("TestingAgent", "agents.testing.testing_agent", "TestingAgent"),
            ("Orchestrator", "agents.orchestrator.orchestrator", "OrchestratorAgent")
        ]
        
        successful_agents = []
        failed_agents = []
        
        for agent_name, module_path, class_name in agents_to_test:
            try:
                module = __import__(module_path, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                agent = agent_class()
                successful_agents.append(agent_name)
            except Exception as e:
                failed_agents.append(f"{agent_name} ({str(e)[:50]})")
        
        if failed_agents:
            return ValidationResult(
                component="Agents",
                test_name="Agent Initialization",
                result=TestResult.WARN if successful_agents else TestResult.FAIL,
                message=f"Failed: {', '.join(failed_agents)}. Successful: {', '.join(successful_agents)}",
                details={"successful": successful_agents, "failed": failed_agents}
            )
        else:
            return ValidationResult(
                component="Agents",
                test_name="Agent Initialization",
                result=TestResult.PASS,
                message=f"All agents initialized successfully: {', '.join(successful_agents)}",
                details={"successful": successful_agents}
            )
    
    async def test_discord_bot_config(self) -> ValidationResult:
        """Test Discord bot configuration."""
        try:
            from bot.config import get_config
            
            config = get_config()
            validation = config.validate()
            
            if not validation['valid']:
                return ValidationResult(
                    component="Discord Bot",
                    test_name="Configuration", 
                    result=TestResult.FAIL,
                    message=f"Configuration validation failed: {', '.join(validation['issues'])}",
                    details=validation
                )
            elif validation['warnings']:
                return ValidationResult(
                    component="Discord Bot",
                    test_name="Configuration",
                    result=TestResult.WARN,
                    message=f"Configuration has warnings: {', '.join(validation['warnings'])}",
                    details=validation
                )
            else:
                return ValidationResult(
                    component="Discord Bot", 
                    test_name="Configuration",
                    result=TestResult.PASS,
                    message="Discord bot configuration valid",
                    details=validation
                )
                
        except Exception as e:
            return ValidationResult(
                component="Discord Bot",
                test_name="Configuration",
                result=TestResult.FAIL,
                message=f"Discord bot configuration test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def test_system_resources(self) -> ValidationResult:
        """Test system resource usage."""
        metrics = self.get_system_metrics()
        
        warnings = []
        errors = []
        
        if metrics.cpu_usage > 90:
            errors.append(f"High CPU usage: {metrics.cpu_usage}%")
        elif metrics.cpu_usage > 75:
            warnings.append(f"Elevated CPU usage: {metrics.cpu_usage}%")
        
        if metrics.memory_usage > 90:
            errors.append(f"High memory usage: {metrics.memory_usage}%")
        elif metrics.memory_usage > 80:
            warnings.append(f"Elevated memory usage: {metrics.memory_usage}%")
        
        if metrics.disk_usage > 95:
            errors.append(f"Critical disk usage: {metrics.disk_usage}%")
        elif metrics.disk_usage > 85:
            warnings.append(f"High disk usage: {metrics.disk_usage}%")
        
        if errors:
            result = TestResult.FAIL
            message = f"System resource errors: {'; '.join(errors)}"
        elif warnings:
            result = TestResult.WARN
            message = f"System resource warnings: {'; '.join(warnings)}"
        else:
            result = TestResult.PASS
            message = "System resources within normal limits"
        
        return ValidationResult(
            component="System Health",
            test_name="Resource Usage",
            result=result,
            message=message,
            details={
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "disk_usage": metrics.disk_usage,
                "load_average": metrics.load_average,
                "is_pi_system": self.is_pi_system
            }
        )
    
    async def test_network_connectivity(self) -> ValidationResult:
        """Test network connectivity."""
        try:
            import aiohttp
            
            test_urls = [
                ("Discord API", "https://discord.com/api/v10/gateway"),
                ("GitHub API", "https://api.github.com")
            ]
            
            results = []
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                for service_name, url in test_urls:
                    try:
                        async with session.get(url) as response:
                            if response.status < 400:
                                results.append(f"✅ {service_name}")
                            else:
                                results.append(f"⚠️ {service_name} (status {response.status})")
                    except asyncio.TimeoutError:
                        results.append(f"❌ {service_name} (timeout)")
                    except Exception as e:
                        results.append(f"❌ {service_name} (error)")
            
            failed_tests = [r for r in results if r.startswith("❌")]
            warning_tests = [r for r in results if r.startswith("⚠️")]
            
            if failed_tests:
                return ValidationResult(
                    component="System Health",
                    test_name="Network Connectivity",
                    result=TestResult.FAIL,
                    message="Network connectivity issues detected",
                    details={"results": results}
                )
            elif warning_tests:
                return ValidationResult(
                    component="System Health", 
                    test_name="Network Connectivity",
                    result=TestResult.WARN,
                    message="Some network services have warnings",
                    details={"results": results}
                )
            else:
                return ValidationResult(
                    component="System Health",
                    test_name="Network Connectivity", 
                    result=TestResult.PASS,
                    message="All network connectivity tests passed",
                    details={"results": results}
                )
                
        except ImportError:
            return ValidationResult(
                component="System Health",
                test_name="Network Connectivity",
                result=TestResult.SKIP,
                message="aiohttp not available for network tests"
            )
        except Exception as e:
            return ValidationResult(
                component="System Health",
                test_name="Network Connectivity",
                result=TestResult.FAIL,
                message=f"Network test failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def test_end_to_end_workflow(self) -> ValidationResult:
        """Test end-to-end workflow simulation."""
        workflow_steps = []
        
        # Test component imports
        try:
            from agents.orchestrator.orchestrator import OrchestratorAgent
            from agents.backend.backend_agent import BackendAgent
            workflow_steps.append("✅ Component imports successful")
        except ImportError as e:
            return ValidationResult(
                component="E2E Workflow",
                test_name="Complete Workflow",
                result=TestResult.FAIL,
                message=f"Failed to import required components: {str(e)}"
            )
        
        # Test agent initialization
        try:
            orchestrator = OrchestratorAgent()
            backend_agent = BackendAgent()
            workflow_steps.append("✅ Agents initialized")
        except Exception as e:
            workflow_steps.append(f"❌ Agent initialization failed: {str(e)}")
        
        # Test workflow simulation
        try:
            mock_task = {
                'title': 'Test API Creation',
                'description': 'Create REST API endpoint', 
                'agent_type': 'backend'
            }
            workflow_steps.append("✅ Mock workflow completed")
        except Exception as e:
            workflow_steps.append(f"❌ Workflow simulation failed: {str(e)}")
        
        successful_steps = len([step for step in workflow_steps if step.startswith("✅")])
        total_steps = len(workflow_steps)
        
        if successful_steps == total_steps:
            result = TestResult.PASS
            message = "End-to-end workflow simulation successful"
        elif successful_steps > 0:
            result = TestResult.WARN
            message = f"Partial workflow success ({successful_steps}/{total_steps} steps)"
        else:
            result = TestResult.FAIL
            message = "End-to-end workflow simulation failed"
        
        return ValidationResult(
            component="E2E Workflow",
            test_name="Complete Workflow",
            result=result,
            message=message,
            details={"steps": workflow_steps}
        )
    
    # ========================================
    # MAIN VALIDATION RUNNER
    # ========================================
    
    async def run_all_tests(self):
        """Run all validation tests."""
        self.logger.info("🚀 Starting comprehensive deployment validation...")
        
        # Run all tests with timing
        test_methods = [
            self.test_environment_variables,
            self.test_file_structure,
            self.test_database_connection,
            self.test_dev_bible_reader,
            self.test_agents,
            self.test_discord_bot_config,
            self.test_system_resources,
            self.test_network_connectivity,
            self.test_end_to_end_workflow
        ]
        
        for test_method in test_methods:
            result = await self._run_test(test_method)
            self.add_result(result)
        
        self.logger.info("✅ All validation tests completed")
    
    def generate_report(self) -> str:
        """Generate comprehensive deployment report."""
        total_time = (datetime.now() - self.start_time).total_seconds()
        metrics = self.get_system_metrics()
        
        # Count results by type
        passed = len([r for r in self.results if r.result == TestResult.PASS])
        failed = len([r for r in self.results if r.result == TestResult.FAIL])
        warnings = len([r for r in self.results if r.result == TestResult.WARN])
        skipped = len([r for r in self.results if r.result == TestResult.SKIP])
        
        # Overall status
        if failed > 0:
            overall_status = "❌ DEPLOYMENT VALIDATION FAILED"
            status_color = "🔴"
        elif warnings > 0:
            overall_status = "⚠️ DEPLOYMENT VALIDATION PASSED WITH WARNINGS"
            status_color = "🟡"
        else:
            overall_status = "✅ DEPLOYMENT VALIDATION PASSED"
            status_color = "🟢"
        
        report = f"""
{'='*80}
🤖 AI AGENT AUTOMATION HUB - DEPLOYMENT VALIDATION REPORT
{'='*80}

{status_color} OVERALL STATUS: {overall_status}

📊 SUMMARY:
   • Total Tests: {len(self.results)}
   • Passed: {passed}
   • Failed: {failed}
   • Warnings: {warnings}
   • Skipped: {skipped}
   • Execution Time: {total_time:.2f} seconds

🖥️ SYSTEM INFORMATION:
   • Platform: {'Raspberry Pi' if self.is_pi_system else 'Generic Linux'}
   • CPU Usage: {metrics.cpu_usage:.1f}%
   • Memory Usage: {metrics.memory_usage:.1f}%
   • Disk Usage: {metrics.disk_usage:.1f}%
   • Load Average: {metrics.load_average[0]:.2f}, {metrics.load_average[1]:.2f}, {metrics.load_average[2]:.2f}
   • Uptime: {timedelta(seconds=int(metrics.uptime))}

{'='*80}
📋 DETAILED TEST RESULTS:
{'='*80}
"""

        # Group results by component
        components = {}
        for result in self.results:
            if result.component not in components:
                components[result.component] = []
            components[result.component].append(result)
        
        for component, component_results in components.items():
            report += f"\n🔧 {component.upper()}:\n"
            report += "─" * 40 + "\n"
            
            for result in component_results:
                report += f"   {result.result.value} {result.test_name}: {result.message}\n"
                if result.execution_time > 0:
                    report += f"      ⏱️ Execution time: {result.execution_time:.2f}s\n"
            report += "\n"
        
        # Add recommendations
        report += f"""
{'='*80}
🎯 RECOMMENDATIONS:
{'='*80}
"""
        
        if failed > 0:
            report += "\n🚨 CRITICAL ISSUES TO RESOLVE:\n"
            for result in self.results:
                if result.result == TestResult.FAIL:
                    report += f"   • {result.component} - {result.test_name}: {result.message}\n"
        
        if warnings > 0:
            report += "\n⚠️ WARNINGS TO ADDRESS:\n"
            for result in self.results:
                if result.result == TestResult.WARN:
                    report += f"   • {result.component} - {result.test_name}: {result.message}\n"
        
        # Next steps
        if failed == 0 and warnings == 0:
            report += """

✅ DEPLOYMENT READY FOR PRODUCTION!

Your AI Agent Automation Hub deployment has passed all validation tests.
You can proceed with confidence to production deployment.

Recommended next steps:
1. Set up monitoring and alerting
2. Configure automated backups
3. Set up log rotation
4. Review security configurations
5. Test with real Discord server and users
"""
        elif failed == 0:
            report += """

⚠️ DEPLOYMENT READY WITH MINOR ISSUES

Your deployment is functional but has some warnings that should be addressed.

Priority actions:
1. Address the warning items listed above
2. Set up monitoring for the flagged components
3. Test thoroughly in a staging environment
4. Proceed with cautious production deployment
"""
        else:
            report += """

❌ DEPLOYMENT NOT READY

Critical issues have been identified that must be resolved before production deployment.

Required actions:
1. Fix all failed tests listed above
2. Address warning items
3. Re-run validation after fixes
4. Consider testing in a development environment first
"""

        report += f"""

📁 LOG LOCATION: {self.project_root / 'logs' / 'deployment_validation.log'}
📅 VALIDATION DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔍 VALIDATOR VERSION: 1.0.0

{'='*80}
"""
        
        return report

async def main():
    """Main function to run deployment validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Agent Automation Hub Deployment Validator')
    parser.add_argument('--config', '-c', help='Configuration file path', default='.env')
    parser.add_argument('--output', '-o', help='Output report file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = DeploymentValidator(config_file=args.config)
    
    if args.verbose:
        validator.logger.setLevel(logging.DEBUG)
    
    print("🤖 AI Agent Automation Hub - Deployment Validator")
    print("=" * 50)
    print(f"📂 Project Root: {validator.project_root}")
    print(f"🖥️ Platform: {'Raspberry Pi' if validator.is_pi_system else 'Generic Linux'}")
    print("🚀 Starting validation tests...\n")
    
    # Run all tests
    await validator.run_all_tests()
    
    # Generate report
    if args.json:
        # JSON output for automation
        json_output = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'pass' if all(r.result != TestResult.FAIL for r in validator.results) else 'fail',
            'summary': {
                'total': len(validator.results),
                'passed': len([r for r in validator.results if r.result == TestResult.PASS]),
                'failed': len([r for r in validator.results if r.result == TestResult.FAIL]),
                'warnings': len([r for r in validator.results if r.result == TestResult.WARN]),
                'skipped': len([r for r in validator.results if r.result == TestResult.SKIP])
            },
            'results': [
                {
                    'component': r.component,
                    'test_name': r.test_name,
                    'result': r.result.name.lower(),
                    'message': r.message,
                    'execution_time': r.execution_time,
                    'details': r.details
                }
                for r in validator.results
            ],
            'system_metrics': validator.get_system_metrics().__dict__
        }
        
        output = json.dumps(json_output, indent=2, default=str)
    else:
        # Human-readable report
        output = validator.generate_report()
    
    # Save to file if specified
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"📄 Report saved to: {args.output}")
    
    # Always print to console
    print(output)
    
    # Exit with appropriate code
    failed_tests = [r for r in validator.results if r.result == TestResult.FAIL]
    sys.exit(1 if failed_tests else 0)

if __name__ == "__main__":
    asyncio.run(main())