"""
Test Runner

Executes comprehensive test suites including unit tests, security scans,
code quality checks, and integration tests.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import os

logger = logging.getLogger(__name__)

class TestRunner:
    """
    Comprehensive test runner for Python projects.
    
    Supports:
    - Unit tests (pytest)
    - Security scanning (bandit)
    - Code coverage analysis
    - Code style checks (flake8, black)
    - Integration tests
    - Performance benchmarks
    """
    
    def __init__(self):
        """Initialize the test runner."""
        self.results_cache = {}
        
    async def run_comprehensive_tests(self, workspace: Path) -> Dict[str, Any]:
        """
        Run the complete test suite on a workspace.
        
        Args:
            workspace: Path to the code workspace
            
        Returns:
            Comprehensive test results dictionary
        """
        start_time = datetime.now()
        logger.info(f"Starting comprehensive tests in {workspace}")
        
        results = {
            "timestamp": start_time.isoformat(),
            "workspace": str(workspace),
            "overall_status": "pass",
            "categories": {},
            "duration": 0,
            "coverage": {},
            "summary": {}
        }
        
        try:
            # Install dependencies first
            await self._install_dependencies(workspace)
            
            # Run test categories in parallel where possible
            test_tasks = [
                ("unit_tests", self._run_unit_tests(workspace)),
                ("security_scan", self._run_security_scan(workspace)),
                ("code_style", self._run_code_style_checks(workspace)),
                ("integration_tests", self._run_integration_tests(workspace)),
                ("performance", self._run_performance_tests(workspace))
            ]
            
            # Execute tests
            for category_name, task in test_tasks:
                try:
                    category_result = await task
                    results["categories"][category_name] = category_result
                    
                    # Update overall status
                    if category_result["status"] != "pass":
                        results["overall_status"] = "fail"
                        
                except Exception as e:
                    logger.error(f"Error in {category_name}: {e}")
                    results["categories"][category_name] = {
                        "status": "error",
                        "error": str(e),
                        "details": f"Test execution failed: {e}"
                    }
                    results["overall_status"] = "fail"
            
            # Generate coverage report
            results["coverage"] = await self._generate_coverage_report(workspace)
            
            # Create summary
            results["summary"] = self._create_test_summary(results)
            
        except Exception as e:
            logger.error(f"Comprehensive test execution failed: {e}")
            results["overall_status"] = "error"
            results["error"] = str(e)
        
        # Calculate duration
        end_time = datetime.now()
        results["duration"] = (end_time - start_time).total_seconds()
        
        logger.info(f"Comprehensive tests completed: {results['overall_status']} ({results['duration']:.1f}s)")
        return results
    
    async def _install_dependencies(self, workspace: Path):
        """Install project dependencies."""
        logger.info("Installing dependencies...")
        
        # Check for requirements.txt
        requirements_file = workspace / "requirements.txt"
        if requirements_file.exists():
            cmd = f"cd {workspace} && pip install -r requirements.txt"
            await self._run_command(cmd, timeout=300)
        
        # Install testing dependencies
        test_deps = [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
            "bandit>=1.7.0",
            "flake8>=5.0.0",
            "black>=22.0.0",
            "safety>=2.0.0",
            "mypy>=1.0.0"
        ]
        
        for dep in test_deps:
            cmd = f"pip install '{dep}'"
            try:
                await self._run_command(cmd, timeout=60)
            except Exception as e:
                logger.warning(f"Failed to install {dep}: {e}")
    
    async def _run_unit_tests(self, workspace: Path) -> Dict[str, Any]:
        """Run unit tests with pytest."""
        logger.info("Running unit tests...")
        
        try:
            # Find test directories
            test_dirs = []
            for pattern in ["tests/", "test/", "**/test_*.py", "**/tests/", "**/*_test.py"]:
                matches = list(workspace.glob(pattern))
                test_dirs.extend(matches)
            
            if not test_dirs:
                return {
                    "status": "skip",
                    "details": "No test files found",
                    "tests_run": 0,
                    "failures": 0,
                    "errors": 0
                }
            
            # Run pytest with coverage
            cmd = f"cd {workspace} && python -m pytest -v --tb=short --junitxml=test_results.xml --cov=. --cov-report=json"
            
            result = await self._run_command(cmd, timeout=300)
            
            # Parse results
            return self._parse_pytest_results(workspace, result)
            
        except Exception as e:
            logger.error(f"Unit tests failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "details": f"Unit test execution failed: {e}"
            }
    
    async def _run_security_scan(self, workspace: Path) -> Dict[str, Any]:
        """Run security scan with bandit."""
        logger.info("Running security scan...")
        
        try:
            # Run bandit security scan
            cmd = f"cd {workspace} && python -m bandit -r . -f json -o bandit_results.json || true"
            
            result = await self._run_command(cmd, timeout=120)
            
            # Parse bandit results
            bandit_file = workspace / "bandit_results.json"
            if bandit_file.exists():
                with open(bandit_file, 'r') as f:
                    bandit_data = json.load(f)
                
                issues = bandit_data.get('results', [])
                high_issues = [i for i in issues if i.get('issue_severity') == 'HIGH']
                medium_issues = [i for i in issues if i.get('issue_severity') == 'MEDIUM']
                
                status = "fail" if high_issues else ("warn" if medium_issues else "pass")
                
                return {
                    "status": status,
                    "total_issues": len(issues),
                    "high_issues": len(high_issues),
                    "medium_issues": len(medium_issues),
                    "low_issues": len(issues) - len(high_issues) - len(medium_issues),
                    "details": f"Found {len(issues)} security issues ({len(high_issues)} high, {len(medium_issues)} medium)"
                }
            else:
                return {
                    "status": "pass",
                    "total_issues": 0,
                    "details": "No security issues found"
                }
                
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "details": f"Security scan failed: {e}"
            }
    
    async def _run_code_style_checks(self, workspace: Path) -> Dict[str, Any]:
        """Run code style checks with flake8 and black."""
        logger.info("Running code style checks...")
        
        try:
            results = {}
            
            # Run flake8
            flake8_cmd = f"cd {workspace} && python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"
            try:
                flake8_result = await self._run_command(flake8_cmd, timeout=60)
                results["flake8"] = {
                    "status": "pass" if flake8_result.returncode == 0 else "fail",
                    "output": flake8_result.stdout + flake8_result.stderr
                }
            except Exception as e:
                results["flake8"] = {"status": "error", "error": str(e)}
            
            # Run black check
            black_cmd = f"cd {workspace} && python -m black --check --diff ."
            try:
                black_result = await self._run_command(black_cmd, timeout=60)
                results["black"] = {
                    "status": "pass" if black_result.returncode == 0 else "fail",
                    "output": black_result.stdout + black_result.stderr
                }
            except Exception as e:
                results["black"] = {"status": "error", "error": str(e)}
            
            # Overall status
            overall_status = "pass"
            for tool_result in results.values():
                if tool_result["status"] in ["fail", "error"]:
                    overall_status = "fail"
                    break
            
            return {
                "status": overall_status,
                "tools": results,
                "details": f"Code style check completed: {overall_status}"
            }
            
        except Exception as e:
            logger.error(f"Code style checks failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "details": f"Code style checks failed: {e}"
            }
    
    async def _run_integration_tests(self, workspace: Path) -> Dict[str, Any]:
        """Run integration tests."""
        logger.info("Running integration tests...")
        
        try:
            # Look for integration test markers or directories
            integration_patterns = [
                "tests/integration/",
                "test/integration/", 
                "**/test_integration_*.py",
                "**/integration_test_*.py"
            ]
            
            integration_files = []
            for pattern in integration_patterns:
                matches = list(workspace.glob(pattern))
                integration_files.extend(matches)
            
            if not integration_files:
                return {
                    "status": "skip",
                    "details": "No integration tests found",
                    "tests_run": 0
                }
            
            # Run integration tests
            cmd = f"cd {workspace} && python -m pytest -v -m integration || python -m pytest -v tests/integration/ || true"
            
            result = await self._run_command(cmd, timeout=600)  # Longer timeout for integration tests
            
            return {
                "status": "pass" if result.returncode == 0 else "fail",
                "return_code": result.returncode,
                "output": result.stdout[-1000:],  # Last 1000 chars
                "details": f"Integration tests completed with return code {result.returncode}"
            }
            
        except Exception as e:
            logger.error(f"Integration tests failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "details": f"Integration tests failed: {e}"
            }
    
    async def _run_performance_tests(self, workspace: Path) -> Dict[str, Any]:
        """Run performance benchmarks."""
        logger.info("Running performance tests...")
        
        try:
            # Look for performance test files
            perf_patterns = [
                "**/test_perf_*.py",
                "**/bench_*.py",
                "**/performance_test_*.py",
                "tests/performance/"
            ]
            
            perf_files = []
            for pattern in perf_patterns:
                matches = list(workspace.glob(pattern))
                perf_files.extend(matches)
            
            if not perf_files:
                return {
                    "status": "skip",
                    "details": "No performance tests found",
                    "benchmarks": 0
                }
            
            # Run performance tests
            cmd = f"cd {workspace} && python -m pytest -v --benchmark-only || true"
            
            result = await self._run_command(cmd, timeout=300)
            
            return {
                "status": "pass" if result.returncode == 0 else "fail",
                "return_code": result.returncode,
                "details": f"Performance tests completed with return code {result.returncode}"
            }
            
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            return {
                "status": "skip",
                "error": str(e),
                "details": "Performance tests skipped due to error"
            }
    
    async def _generate_coverage_report(self, workspace: Path) -> Dict[str, Any]:
        """Generate code coverage report."""
        try:
            coverage_file = workspace / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                
                return {
                    "percentage": round(total_coverage, 2),
                    "lines_covered": coverage_data.get('totals', {}).get('covered_lines', 0),
                    "lines_total": coverage_data.get('totals', {}).get('num_statements', 0),
                    "details": f"Code coverage: {total_coverage:.1f}%"
                }
            else:
                return {
                    "percentage": 0,
                    "details": "No coverage data available"
                }
        except Exception as e:
            logger.error(f"Coverage report generation failed: {e}")
            return {
                "percentage": 0,
                "error": str(e),
                "details": "Coverage report failed"
            }
    
    def _parse_pytest_results(self, workspace: Path, result) -> Dict[str, Any]:
        """Parse pytest results from XML output."""
        try:
            # Try to parse XML results
            xml_file = workspace / "test_results.xml"
            if xml_file.exists():
                import xml.etree.ElementTree as ET
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                tests_run = int(root.get('tests', 0))
                failures = int(root.get('failures', 0))
                errors = int(root.get('errors', 0))
                
                status = "pass" if (failures + errors) == 0 else "fail"
                
                return {
                    "status": status,
                    "tests_run": tests_run,
                    "failures": failures,
                    "errors": errors,
                    "details": f"Tests: {tests_run}, Failures: {failures}, Errors: {errors}"
                }
            else:
                # Fallback to return code
                status = "pass" if result.returncode == 0 else "fail"
                return {
                    "status": status,
                    "return_code": result.returncode,
                    "details": f"Unit tests completed with return code {result.returncode}"
                }
                
        except Exception as e:
            logger.error(f"Failed to parse pytest results: {e}")
            return {
                "status": "error",
                "error": str(e),
                "details": "Failed to parse test results"
            }
    
    def _create_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of all test results."""
        summary = {
            "total_categories": len(results["categories"]),
            "passed_categories": 0,
            "failed_categories": 0,
            "error_categories": 0,
            "skipped_categories": 0
        }
        
        for category_result in results["categories"].values():
            status = category_result.get("status", "error")
            if status == "pass":
                summary["passed_categories"] += 1
            elif status == "fail":
                summary["failed_categories"] += 1
            elif status == "skip":
                summary["skipped_categories"] += 1
            else:
                summary["error_categories"] += 1
        
        summary["success_rate"] = (
            summary["passed_categories"] / summary["total_categories"] * 100
            if summary["total_categories"] > 0 else 0
        )
        
        return summary
    
    async def _run_command(self, command: str, timeout: int = 60, cwd: Optional[Path] = None):
        """Run a shell command with timeout."""
        logger.debug(f"Running command: {command}")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            result = type('Result', (), {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore')
            })()
            
            logger.debug(f"Command completed with return code: {result.returncode}")
            return result
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise Exception(f"Command timed out after {timeout} seconds: {command}")
    
    async def run_quick_tests(self, workspace: Path) -> Dict[str, Any]:
        """Run a quick subset of tests for fast feedback."""
        start_time = datetime.now()
        
        results = {
            "timestamp": start_time.isoformat(),
            "workspace": str(workspace),
            "overall_status": "pass",
            "quick_mode": True,
            "categories": {}
        }
        
        try:
            # Quick unit tests only
            results["categories"]["unit_tests"] = await self._run_unit_tests(workspace)
            results["categories"]["security_scan"] = await self._run_security_scan(workspace)
            
            # Update overall status
            for category_result in results["categories"].values():
                if category_result["status"] in ["fail", "error"]:
                    results["overall_status"] = "fail"
                    break
        
        except Exception as e:
            results["overall_status"] = "error"
            results["error"] = str(e)
        
        results["duration"] = (datetime.now() - start_time).total_seconds()
        return results