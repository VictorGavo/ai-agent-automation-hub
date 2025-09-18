# agents/backend/task_executor.py
"""Core task execution logic with Flask specialization"""

import asyncio
import ast
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

from database.models.task import Task, TaskCategory
from database.models.logs import Log, LogLevel

logger = logging.getLogger(__name__)

class TaskExecutor:
    """
    Executes backend development tasks with these capabilities:
    - Flask route creation
    - Database model integration  
    - API endpoint implementation
    - Error handling and validation
    - Test generation
    """
    
    def __init__(self, agent_name: str = "backend-agent"):
        self.agent_name = agent_name
        self.project_root = Path.cwd()
        self.app_dir = self.project_root / "app"
        self.tests_dir = self.project_root / "tests"
        
        # Task execution statistics
        self.stats = {
            "tasks_executed": 0,
            "endpoints_created": 0,
            "tests_generated": 0,
            "tests_passed": 0,
            "validation_failures": 0,
            "execution_errors": 0
        }
        
        # Code generation templates
        self.templates = {
            "flask_route": self._get_flask_route_template(),
            "test_case": self._get_test_template(),
            "model_integration": self._get_model_template()
        }
        
        logger.info(f"TaskExecutor initialized for agent: {self.agent_name}")
    
    async def execute_flask_endpoint(self, task: Task) -> Dict[str, Any]:
        """
        Parse endpoint requirements from task description and implement Flask route
        
        Args:
            task: Task object containing endpoint requirements
            
        Returns:
            Dictionary with implementation details and results
        """
        try:
            logger.info(f"Executing Flask endpoint task: {task.id}")
            
            # Parse endpoint requirements from task description
            endpoint_spec = await self._parse_endpoint_requirements(task)
            
            # Generate Flask route code
            flask_code = await self.generate_flask_code(endpoint_spec)
            
            # Generate corresponding test cases
            test_code = await self._generate_test_code(endpoint_spec)
            
            # Determine file paths
            route_file = self._determine_route_file(endpoint_spec)
            test_file = self._determine_test_file(endpoint_spec)
            
            # Validate generated code
            validation_result = await self.validate_implementation(task, flask_code)
            
            # Prepare implementation details
            implementation = {
                "files": {
                    route_file: flask_code,
                    test_file: test_code
                },
                "endpoint_spec": endpoint_spec,
                "validation_passed": validation_result,
                "route_path": endpoint_spec.get("route", "/api/endpoint"),
                "http_method": endpoint_spec.get("method", "GET"),
                "function_name": endpoint_spec.get("function_name", "new_endpoint")
            }
            
            # Update statistics
            self.stats["tasks_executed"] += 1
            self.stats["endpoints_created"] += 1
            self.stats["tests_generated"] += 1
            
            if validation_result:
                logger.info(f"Flask endpoint implementation completed successfully for task {task.id}")
            else:
                logger.warning(f"Flask endpoint implementation completed with validation warnings for task {task.id}")
                self.stats["validation_failures"] += 1
            
            return {
                "success": True,
                "implementation": implementation,
                "message": f"Flask endpoint '{endpoint_spec.get('route')}' implemented successfully",
                "files_created": len(implementation["files"]),
                "validation_passed": validation_result
            }
            
        except Exception as e:
            logger.error(f"Flask endpoint execution failed for task {task.id}: {e}")
            self.stats["execution_errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute Flask endpoint task: {str(e)[:100]}..."
            }
    
    async def generate_flask_code(self, endpoint_spec: Dict) -> str:
        """
        Generate Flask route code following project standards
        
        Args:
            endpoint_spec: Dictionary containing endpoint specifications
            
        Returns:
            Generated Flask route code as string
        """
        try:
            # Extract endpoint details
            route = endpoint_spec.get("route", "/api/endpoint")
            method = endpoint_spec.get("method", "GET").upper()
            function_name = endpoint_spec.get("function_name", "new_endpoint")
            description = endpoint_spec.get("description", "Generated API endpoint")
            requires_auth = endpoint_spec.get("requires_auth", False)
            requires_db = endpoint_spec.get("requires_db", True)
            request_schema = endpoint_spec.get("request_schema", {})
            response_schema = endpoint_spec.get("response_schema", {})
            
            # Build imports
            imports = self._build_imports(endpoint_spec)
            
            # Build route decorator
            route_decorator = f"@api_bp.route('{route}', methods=['{method}'])"
            
            # Build function signature
            function_signature = f"def {function_name}():"
            
            # Build docstring
            docstring = self._build_docstring(description, method, route, request_schema, response_schema)
            
            # Build function body
            function_body = self._build_function_body(endpoint_spec)
            
            # Combine all parts
            flask_code = f"""{imports}

{route_decorator}
{function_signature}
    \"\"\"
{docstring}
    \"\"\"
{function_body}
"""
            
            logger.debug(f"Generated Flask code for route {route}")
            return flask_code
            
        except Exception as e:
            logger.error(f"Flask code generation failed: {e}")
            raise
    
    async def run_tests(self, modified_files: List[str]) -> Dict[str, bool]:
        """
        Run pytest on modified code and check existing tests
        
        Args:
            modified_files: List of file paths that were modified
            
        Returns:
            Dictionary with test results and coverage info
        """
        try:
            logger.info(f"Running tests for modified files: {modified_files}")
            
            results = {
                "tests_executed": False,
                "all_tests_passed": False,
                "new_tests_passed": False,
                "coverage_acceptable": False,
                "test_output": "",
                "coverage_percentage": 0.0
            }
            
            # Check if pytest is available
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    logger.warning("pytest not available - skipping test execution")
                    return results
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("pytest not available - skipping test execution")
                return results
            
            # Run tests for specific files
            test_files = []
            for file_path in modified_files:
                if file_path.startswith("tests/"):
                    test_files.append(file_path)
                else:
                    # Find corresponding test file
                    test_file = self._find_test_file(file_path)
                    if test_file:
                        test_files.append(test_file)
            
            if not test_files:
                logger.info("No test files found for modified files")
                return results
            
            # Execute tests
            try:
                cmd = ["python", "-m", "pytest", "-v"] + test_files
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(self.project_root)
                )
                
                results["tests_executed"] = True
                results["test_output"] = result.stdout + result.stderr
                results["all_tests_passed"] = result.returncode == 0
                
                # Parse test results
                if "passed" in result.stdout:
                    passed_count = len(re.findall(r"PASSED", result.stdout))
                    failed_count = len(re.findall(r"FAILED", result.stdout))
                    results["new_tests_passed"] = failed_count == 0
                    
                    logger.info(f"Test results: {passed_count} passed, {failed_count} failed")
                    
                    if results["all_tests_passed"]:
                        self.stats["tests_passed"] += passed_count
                
            except subprocess.TimeoutExpired:
                logger.warning("Test execution timed out")
                results["test_output"] = "Test execution timed out after 60 seconds"
            
            return results
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "tests_executed": False,
                "all_tests_passed": False,
                "new_tests_passed": False,
                "coverage_acceptable": False,
                "test_output": f"Test execution error: {str(e)}",
                "coverage_percentage": 0.0
            }
    
    async def validate_implementation(self, task: Task, implementation: str) -> bool:
        """
        Check implementation against success criteria and project standards
        
        Args:
            task: Task object with success criteria
            implementation: Generated code to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            logger.debug(f"Validating implementation for task {task.id}")
            
            validation_checks = []
            
            # 1. Syntax validation
            try:
                ast.parse(implementation)
                validation_checks.append(("syntax_valid", True))
                logger.debug("Syntax validation passed")
            except SyntaxError as e:
                validation_checks.append(("syntax_valid", False))
                logger.error(f"Syntax validation failed: {e}")
            
            # 2. Required imports validation
            required_imports = ["flask", "jsonify"]
            for import_name in required_imports:
                if import_name in implementation.lower():
                    validation_checks.append((f"import_{import_name}", True))
                else:
                    validation_checks.append((f"import_{import_name}", False))
                    logger.warning(f"Missing required import: {import_name}")
            
            # 3. Error handling validation
            error_handling_patterns = ["try:", "except", "return jsonify"]
            error_handling_found = any(pattern in implementation for pattern in error_handling_patterns)
            validation_checks.append(("error_handling", error_handling_found))
            
            if not error_handling_found:
                logger.warning("No error handling patterns found in implementation")
            
            # 4. Security validation
            security_issues = []
            
            # Check for SQL injection vulnerabilities
            if re.search(r'execute\s*\(["\'][^"\']*%[^"\']*["\']', implementation):
                security_issues.append("potential_sql_injection")
            
            # Check for direct string interpolation in queries
            if re.search(r'["\'][^"\']*\{[^}]*\}[^"\']*["\']', implementation):
                security_issues.append("string_interpolation_in_query")
            
            validation_checks.append(("security_safe", len(security_issues) == 0))
            
            if security_issues:
                logger.warning(f"Security issues found: {security_issues}")
            
            # 5. Success criteria validation
            success_criteria = task.success_criteria or []
            criteria_met = 0
            
            for criteria in success_criteria:
                criteria_lower = criteria.lower()
                # Basic keyword matching for success criteria
                if any(keyword in implementation.lower() for keyword in criteria_lower.split()):
                    criteria_met += 1
            
            criteria_percentage = (criteria_met / max(len(success_criteria), 1)) * 100
            validation_checks.append(("success_criteria_met", criteria_percentage >= 70))
            
            logger.debug(f"Success criteria: {criteria_met}/{len(success_criteria)} met ({criteria_percentage:.1f}%)")
            
            # 6. Code quality checks
            quality_checks = [
                ("docstring_present", '"""' in implementation or "'''" in implementation),
                ("function_name_valid", re.search(r'def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(', implementation) is not None),
                ("return_statement_present", "return" in implementation),
                ("proper_indentation", "    " in implementation)  # Basic indentation check
            ]
            
            validation_checks.extend(quality_checks)
            
            # Calculate overall validation score
            passed_checks = sum(1 for check, result in validation_checks if result)
            total_checks = len(validation_checks)
            validation_score = (passed_checks / total_checks) * 100
            
            logger.info(f"Validation score: {passed_checks}/{total_checks} ({validation_score:.1f}%)")
            
            # Pass if 80% of checks pass
            validation_passed = validation_score >= 80
            
            if not validation_passed:
                self.stats["validation_failures"] += 1
                logger.warning(f"Validation failed with score {validation_score:.1f}%")
            
            return validation_passed
            
        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            self.stats["validation_failures"] += 1
            return False
    
    async def _parse_endpoint_requirements(self, task: Task) -> Dict[str, Any]:
        """Parse task description to extract endpoint requirements"""
        try:
            description = task.description.lower()
            
            # Default endpoint specification
            endpoint_spec = {
                "route": "/api/endpoint",
                "method": "GET",
                "function_name": "new_endpoint",
                "description": task.description,
                "requires_auth": False,
                "requires_db": True,
                "request_schema": {},
                "response_schema": {},
                "task_id": str(task.id),
                "task_title": task.title
            }
            
            # Extract HTTP method
            methods = ["POST", "GET", "PUT", "DELETE", "PATCH"]
            for method in methods:
                if method.lower() in description:
                    endpoint_spec["method"] = method
                    break
            
            # Extract route from description
            route_patterns = [
                r'/api/[\w/\-]+',
                r'/[\w/\-]+',
                r'endpoint\s+["\']([^"\']+)["\']',
                r'route\s+["\']([^"\']+)["\']'
            ]
            
            for pattern in route_patterns:
                match = re.search(pattern, task.description)
                if match:
                    route = match.group(1) if match.groups() else match.group(0)
                    if route.startswith('/'):
                        endpoint_spec["route"] = route
                    break
            
            # Generate function name from title
            function_name = re.sub(r'[^a-zA-Z0-9_]', '_', task.title.lower())
            function_name = re.sub(r'_+', '_', function_name).strip('_')
            if function_name:
                endpoint_spec["function_name"] = function_name
            
            # Check for authentication requirements
            auth_keywords = ["auth", "login", "token", "permission", "user"]
            endpoint_spec["requires_auth"] = any(keyword in description for keyword in auth_keywords)
            
            # Check for database requirements
            db_keywords = ["database", "db", "model", "save", "create", "update", "delete"]
            endpoint_spec["requires_db"] = any(keyword in description for keyword in db_keywords)
            
            # Extract additional details from task metadata
            if task.task_metadata:
                metadata = task.task_metadata
                endpoint_spec.update({
                    "request_schema": metadata.get("request_schema", {}),
                    "response_schema": metadata.get("response_schema", {}),
                    "requires_auth": metadata.get("requires_auth", endpoint_spec["requires_auth"]),
                    "requires_db": metadata.get("requires_db", endpoint_spec["requires_db"])
                })
            
            logger.debug(f"Parsed endpoint specification: {endpoint_spec}")
            return endpoint_spec
            
        except Exception as e:
            logger.error(f"Failed to parse endpoint requirements: {e}")
            # Return default spec on error
            return {
                "route": "/api/endpoint",
                "method": "GET",
                "function_name": "new_endpoint",
                "description": task.description,
                "requires_auth": False,
                "requires_db": True,
                "request_schema": {},
                "response_schema": {},
                "task_id": str(task.id),
                "task_title": task.title
            }
    
    def _build_imports(self, endpoint_spec: Dict) -> str:
        """Build import statements based on endpoint requirements"""
        imports = [
            "from flask import Blueprint, request, jsonify",
            "from datetime import datetime, timezone",
            "from typing import Dict, Any, Optional",
            "import logging"
        ]
        
        if endpoint_spec.get("requires_db", True):
            imports.extend([
                "from database.models.base import get_db",
                "from sqlalchemy.orm import Session",
                "from sqlalchemy.exc import SQLAlchemyError"
            ])
        
        if endpoint_spec.get("requires_auth", False):
            imports.append("from auth.decorators import require_auth")
        
        return "\n".join(imports)
    
    def _build_docstring(self, description: str, method: str, route: str, 
                        request_schema: Dict, response_schema: Dict) -> str:
        """Build comprehensive docstring for the endpoint"""
        docstring = f"    {description}\n    \n"
        docstring += f"    Route: {method} {route}\n    \n"
        
        if method in ["POST", "PUT", "PATCH"] and request_schema:
            docstring += "    Request Body:\n"
            for field, field_type in request_schema.items():
                docstring += f"        {field} ({field_type}): Field description\n"
            docstring += "    \n"
        
        docstring += "    Returns:\n"
        docstring += "        JSON response with operation result\n    \n"
        docstring += "    Raises:\n"
        docstring += "        400: Bad Request - Invalid input data\n"
        docstring += "        500: Internal Server Error - Server processing error"
        
        return docstring
    
    def _build_function_body(self, endpoint_spec: Dict) -> str:
        """Build the main function body based on endpoint specifications"""
        method = endpoint_spec.get("method", "GET")
        requires_db = endpoint_spec.get("requires_db", True)
        requires_auth = endpoint_spec.get("requires_auth", False)
        
        body_lines = []
        
        # Add logger
        body_lines.append("    logger = logging.getLogger(__name__)")
        body_lines.append("    ")
        
        # Add try block
        body_lines.append("    try:")
        
        # Database session setup
        if requires_db:
            body_lines.append("        db: Session = next(get_db())")
            body_lines.append("        ")
        
        # Request data handling for POST/PUT/PATCH
        if method in ["POST", "PUT", "PATCH"]:
            body_lines.extend([
                "        # Extract and validate request data",
                "        if not request.is_json:",
                "            return jsonify({",
                "                \"success\": False,",
                "                \"error\": \"Content-Type must be application/json\"",
                "            }), 400",
                "        ",
                "        data = request.get_json()",
                "        if not data:",
                "            return jsonify({",
                "                \"success\": False,",
                "                \"error\": \"Invalid JSON data\"",
                "            }), 400",
                "        "
            ])
        
        # Main business logic placeholder
        body_lines.extend([
            "        # TODO: Implement business logic here",
            "        # This is a generated endpoint - customize as needed",
            "        ",
            "        result = {",
            "            \"success\": True,",
            f"            \"message\": \"{endpoint_spec.get('function_name', 'endpoint')} executed successfully\",",
            "            \"data\": {},",
            "            \"timestamp\": datetime.now(timezone.utc).isoformat()",
            "        }",
            "        ",
            "        logger.info(f\"Endpoint executed successfully: {result['message']}\")",
            "        return jsonify(result), 200",
            "        "
        ])
        
        # Exception handling
        if requires_db:
            body_lines.extend([
                "    except SQLAlchemyError as e:",
                "        logger.error(f\"Database error: {e}\")",
                "        if 'db' in locals():",
                "            db.rollback()",
                "        return jsonify({",
                "            \"success\": False,",
                "            \"error\": \"Database operation failed\",",
                "            \"timestamp\": datetime.now(timezone.utc).isoformat()",
                "        }), 500",
                "        "
            ])
        
        body_lines.extend([
            "    except ValueError as e:",
            "        logger.warning(f\"Validation error: {e}\")",
            "        return jsonify({",
            "            \"success\": False,",
            "            \"error\": str(e),",
            "            \"timestamp\": datetime.now(timezone.utc).isoformat()",
            "        }), 400",
            "        ",
            "    except Exception as e:",
            "        logger.error(f\"Unexpected error: {e}\")",
            "        return jsonify({",
            "            \"success\": False,",
            "            \"error\": \"Internal server error\",",
            "            \"timestamp\": datetime.now(timezone.utc).isoformat()",
            "        }), 500"
        ])
        
        if requires_db:
            body_lines.extend([
                "    finally:",
                "        if 'db' in locals():",
                "            db.close()"
            ])
        
        return "\n".join(body_lines)
    
    async def _generate_test_code(self, endpoint_spec: Dict) -> str:
        """Generate test code for the endpoint"""
        function_name = endpoint_spec.get("function_name", "new_endpoint")
        route = endpoint_spec.get("route", "/api/endpoint")
        method = endpoint_spec.get("method", "GET")
        
        test_code = f"""
import pytest
import json
from flask import Flask
from unittest.mock import patch, MagicMock

# Test for {function_name} endpoint

@pytest.fixture
def client():
    \"\"\"Create test client fixture\"\"\"
    from app import create_app
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_{function_name}_success(client):
    \"\"\"Test successful {function_name} execution\"\"\"
    {self._generate_test_method_call(method, route)}
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'message' in data
    assert 'timestamp' in data

def test_{function_name}_error_handling(client):
    \"\"\"Test error handling for {function_name}\"\"\"
    {self._generate_error_test_call(method, route)}
    
    assert response.status_code in [400, 422, 500]
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data

@patch('database.models.base.get_db')
def test_{function_name}_database_error(mock_get_db, client):
    \"\"\"Test database error handling\"\"\"
    # Mock database session that raises an exception
    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Database connection failed")
    mock_get_db.return_value = iter([mock_session])
    
    {self._generate_test_method_call(method, route)}
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['success'] is False
"""
        
        return test_code.strip()
    
    def _generate_test_method_call(self, method: str, route: str) -> str:
        """Generate appropriate test method call based on HTTP method"""
        if method.upper() == "GET":
            return f"response = client.get('{route}')"
        elif method.upper() == "POST":
            return f"""response = client.post('{route}', 
                               json={{"test": "data"}},
                               content_type='application/json')"""
        elif method.upper() == "PUT":
            return f"""response = client.put('{route}', 
                              json={{"test": "data"}},
                              content_type='application/json')"""
        elif method.upper() == "DELETE":
            return f"response = client.delete('{route}')"
        else:
            return f"response = client.{method.lower()}('{route}')"
    
    def _generate_error_test_call(self, method: str, route: str) -> str:
        """Generate test call that should trigger error"""
        if method.upper() in ["POST", "PUT", "PATCH"]:
            return f"response = client.{method.lower()}('{route}', data='invalid json')"
        else:
            return f"response = client.{method.lower()}('{route}')"
    
    def _determine_route_file(self, endpoint_spec: Dict) -> str:
        """Determine appropriate file path for the route"""
        function_name = endpoint_spec.get("function_name", "new_endpoint")
        route = endpoint_spec.get("route", "/api/endpoint")
        
        # Extract category from route
        if route.startswith("/api/"):
            category = route.split("/")[2] if len(route.split("/")) > 2 else "general"
        else:
            category = "general"
        
        return f"app/routes/{category}.py"
    
    def _determine_test_file(self, endpoint_spec: Dict) -> str:
        """Determine appropriate test file path"""
        function_name = endpoint_spec.get("function_name", "new_endpoint")
        return f"tests/test_{function_name}.py"
    
    def _find_test_file(self, file_path: str) -> Optional[str]:
        """Find corresponding test file for a given source file"""
        if file_path.startswith("app/"):
            # Convert app/routes/users.py -> tests/test_users.py
            filename = Path(file_path).stem
            return f"tests/test_{filename}.py"
        return None
    
    def _get_flask_route_template(self) -> str:
        """Get Flask route template"""
        return """
@api_bp.route('{route}', methods=['{method}'])
def {function_name}():
    \"\"\"
    {description}
    \"\"\"
    try:
        # Implementation here
        return jsonify({{"success": True}}), 200
    except Exception as e:
        return jsonify({{"success": False, "error": str(e)}}), 500
"""
    
    def _get_test_template(self) -> str:
        """Get test template"""
        return """
def test_{function_name}(client):
    \"\"\"Test {function_name} endpoint\"\"\"
    response = client.{method}('{route}')
    assert response.status_code == 200
"""
    
    def _get_model_template(self) -> str:
        """Get SQLAlchemy model template"""
        return """
from sqlalchemy import Column, String, Integer
from database.models.base import Base

class {model_name}(Base):
    __tablename__ = "{table_name}"
    
    id = Column(Integer, primary_key=True)
    # Add fields here
"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task execution statistics"""
        return {
            "task_executor_stats": self.stats.copy(),
            "success_rate": self._calculate_success_rate(),
            "agent_name": self.agent_name,
            "project_root": str(self.project_root)
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of task executions"""
        total_tasks = self.stats["tasks_executed"]
        if total_tasks == 0:
            return 100.0
        
        failed_tasks = self.stats["execution_errors"] + self.stats["validation_failures"]
        successful_tasks = total_tasks - failed_tasks
        return (successful_tasks / total_tasks) * 100.0

# Blueprint setup helper
def create_api_blueprint() -> str:
    """Generate code for API blueprint setup"""
    return '''
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import route modules here
# from . import users, auth, general
'''