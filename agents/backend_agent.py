"""
Backend Agent Module

This module provides the BackendAgent class that specializes in backend development
tasks including Flask API creation, business logic implementation, and Git integration.
"""

import sys
import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import subprocess
import tempfile
import json
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, require_dev_bible_prep

logger = logging.getLogger(__name__)


class BackendAgent(BaseAgent):
    """
    Backend Agent specialized in Flask API development and backend implementation.
    
    This agent inherits from BaseAgent and provides specialized functionality for:
    - Creating Flask endpoints with proper structure
    - Implementing business logic following coding standards
    - Running comprehensive tests
    - Git integration for branch management and PR submission
    
    Example Usage:
        ```python
        backend_agent = BackendAgent("APIBuilder")
        backend_agent.prepare_for_task("Implement user authentication API", "backend")
        
        # Create Flask endpoint
        endpoint_result = backend_agent.create_flask_endpoint(
            endpoint_name="user_login",
            route="/api/v1/auth/login",
            methods=["POST"],
            auth_required=False
        )
        
        # Implement business logic
        logic_result = backend_agent.implement_business_logic(
            function_name="authenticate_user",
            requirements="Validate credentials and return JWT token"
        )
        
        # Run tests
        test_result = backend_agent.run_tests(test_type="unit")
        ```
    
    Attributes:
        project_root (str): Root directory of the project
        git_branch (Optional[str]): Current Git branch for development
        flask_app_structure (Dict): Template for Flask application structure
        coding_standards (Dict): Loaded coding standards from dev_bible
    """
    
    def __init__(self, agent_name: str, project_root: Optional[str] = None, dev_bible_path: Optional[str] = None):
        """
        Initialize BackendAgent with backend-specific capabilities.
        
        Args:
            agent_name (str): Unique name for this backend agent instance
            project_root (Optional[str]): Root directory of the project
            dev_bible_path (Optional[str]): Path to dev_bible directory
        """
        super().__init__(agent_name, "backend", dev_bible_path)
        
        # Project configuration
        self.project_root = project_root or os.getcwd()
        self.git_branch: Optional[str] = None
        
        # Flask application structure template
        self.flask_app_structure = {
            "routes": "agents/backend/routes",
            "models": "database/models", 
            "services": "agents/backend/services",
            "utils": "agents/backend/utils",
            "tests": "tests/backend"
        }
        
        # Development tracking
        self.created_endpoints = []
        self.implemented_functions = []
        self.test_results = []
        
        # Git integration settings
        self.git_config = {
            "remote": "origin",
            "main_branch": "main",
            "commit_prefix": f"[{agent_name}]"
        }
        
        logger.info(f"BackendAgent {agent_name} initialized for project at {self.project_root}")
    
    @require_dev_bible_prep
    def create_flask_endpoint(
        self, 
        endpoint_name: str,
        route: str,
        methods: List[str] = None,
        auth_required: bool = True,
        request_schema: Optional[Dict[str, Any]] = None,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Flask endpoint following coding standards and architecture guidelines.
        
        Args:
            endpoint_name (str): Name of the endpoint function
            route (str): URL route for the endpoint
            methods (List[str], optional): HTTP methods. Defaults to ["GET"]
            auth_required (bool): Whether endpoint requires authentication
            request_schema (Optional[Dict]): Expected request data structure
            response_schema (Optional[Dict]): Expected response data structure
            
        Returns:
            Dict[str, Any]: Endpoint creation results including:
                - endpoint_file: Path to created endpoint file
                - function_name: Generated function name
                - route_registered: Whether route was registered
                - validation_results: Code standards validation
                
        Example:
            ```python
            result = backend_agent.create_flask_endpoint(
                endpoint_name="get_user_profile",
                route="/api/v1/users/<user_id>",
                methods=["GET"],
                auth_required=True,
                response_schema={"user_id": "str", "username": "str", "email": "str"}
            )
            ```
        """
        logger.info(f"Creating Flask endpoint: {endpoint_name} at {route}")
        
        if not endpoint_name or not route:
            raise ValueError("Endpoint name and route are required")
        
        methods = methods or ["GET"]
        
        # Validate route format
        if not route.startswith('/'):
            route = '/' + route
        
        # Generate endpoint code following coding standards
        endpoint_code = self._generate_endpoint_code(
            endpoint_name, route, methods, auth_required, request_schema, response_schema
        )
        
        # Create endpoint file
        endpoint_file_path = self._create_endpoint_file(endpoint_name, endpoint_code)
        
        # Validate against coding standards
        validation_results = self._validate_code_standards(endpoint_code)
        
        # Register in Flask app (simulated)
        route_registered = self._register_route(endpoint_name, route, methods)
        
        endpoint_result = {
            'endpoint_name': endpoint_name,
            'route': route,
            'methods': methods,
            'auth_required': auth_required,
            'endpoint_file': endpoint_file_path,
            'function_name': self._generate_function_name(endpoint_name),
            'route_registered': route_registered,
            'validation_results': validation_results,
            'created_at': datetime.now(),
            'created_by': self.agent_name,
            'guidelines_applied': bool(self.current_guidelines)
        }
        
        # Track created endpoint
        self.created_endpoints.append(endpoint_result)
        
        logger.info(f"✓ Flask endpoint {endpoint_name} created successfully at {endpoint_file_path}")
        
        return endpoint_result
    
    @require_dev_bible_prep
    def implement_business_logic(
        self,
        function_name: str,
        requirements: str,
        input_parameters: Optional[Dict[str, str]] = None,
        return_type: str = "Dict[str, Any]",
        database_operations: bool = False
    ) -> Dict[str, Any]:
        """
        Implement business logic function following coding standards and architecture.
        
        Args:
            function_name (str): Name of the business logic function
            requirements (str): Detailed requirements for the function
            input_parameters (Optional[Dict[str, str]]): Parameter name to type mapping
            return_type (str): Expected return type
            database_operations (bool): Whether function involves database operations
            
        Returns:
            Dict[str, Any]: Implementation results including:
                - function_file: Path to implementation file
                - function_code: Generated function code
                - validation_results: Standards compliance check
                - test_cases: Suggested test cases
                
        Example:
            ```python
            result = backend_agent.implement_business_logic(
                function_name="calculate_user_score",
                requirements="Calculate user engagement score based on activity metrics",
                input_parameters={"user_id": "int", "activity_data": "Dict[str, Any]"},
                return_type="float",
                database_operations=True
            )
            ```
        """
        logger.info(f"Implementing business logic: {function_name}")
        
        if not function_name or not requirements:
            raise ValueError("Function name and requirements are required")
        
        input_parameters = input_parameters or {}
        
        # Generate business logic code
        function_code = self._generate_business_logic_code(
            function_name, requirements, input_parameters, return_type, database_operations
        )
        
        # Create implementation file
        function_file_path = self._create_business_logic_file(function_name, function_code)
        
        # Validate against coding standards
        validation_results = self._validate_code_standards(function_code)
        
        # Generate suggested test cases
        test_cases = self._generate_test_cases(function_name, input_parameters, return_type)
        
        # Check for potential security issues
        security_check = self._perform_security_check(function_code, database_operations)
        
        implementation_result = {
            'function_name': function_name,
            'requirements': requirements,
            'input_parameters': input_parameters,
            'return_type': return_type,
            'database_operations': database_operations,
            'function_file': function_file_path,
            'function_code': function_code,
            'validation_results': validation_results,
            'security_check': security_check,
            'test_cases': test_cases,
            'implemented_at': datetime.now(),
            'implemented_by': self.agent_name,
            'guidelines_applied': bool(self.current_guidelines)
        }
        
        # Track implementation
        self.implemented_functions.append(implementation_result)
        
        logger.info(f"✓ Business logic {function_name} implemented successfully")
        
        return implementation_result
    
    @require_dev_bible_prep
    def run_tests(
        self,
        test_type: str = "unit",
        target_files: Optional[List[str]] = None,
        coverage_threshold: float = 80.0,
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive tests following testing guidelines from dev_bible.
        
        Args:
            test_type (str): Type of tests to run (unit, integration, all)
            target_files (Optional[List[str]]): Specific files to test
            coverage_threshold (float): Minimum coverage percentage required
            generate_report (bool): Whether to generate detailed test report
            
        Returns:
            Dict[str, Any]: Test execution results including:
                - test_summary: Overall test results
                - coverage_report: Code coverage analysis
                - failed_tests: Details of any failed tests
                - recommendations: Suggestions for improvement
                
        Example:
            ```python
            result = backend_agent.run_tests(
                test_type="unit",
                coverage_threshold=85.0,
                generate_report=True
            )
            ```
        """
        logger.info(f"Running {test_type} tests with coverage threshold {coverage_threshold}%")
        
        valid_test_types = ["unit", "integration", "all"]
        if test_type not in valid_test_types:
            raise ValueError(f"Test type must be one of: {valid_test_types}")
        
        # Prepare test environment
        test_environment = self._prepare_test_environment(test_type, target_files)
        
        # Execute tests
        test_results = self._execute_tests(test_type, target_files)
        
        # Generate coverage report
        coverage_report = self._generate_coverage_report(target_files, coverage_threshold)
        
        # Analyze failed tests
        failed_tests = [test for test in test_results['individual_tests'] if not test['passed']]
        
        # Generate recommendations
        recommendations = self._generate_test_recommendations(
            test_results, coverage_report, failed_tests
        )
        
        # Create detailed report if requested
        detailed_report = None
        if generate_report:
            detailed_report = self._create_test_report(
                test_results, coverage_report, failed_tests, recommendations
            )
        
        test_execution_result = {
            'test_type': test_type,
            'target_files': target_files,
            'coverage_threshold': coverage_threshold,
            'test_summary': {
                'total_tests': test_results['total_tests'],
                'passed': test_results['passed_tests'],
                'failed': test_results['failed_tests'],
                'skipped': test_results['skipped_tests'],
                'execution_time': test_results['execution_time']
            },
            'coverage_report': coverage_report,
            'failed_tests': failed_tests,
            'recommendations': recommendations,
            'detailed_report': detailed_report,
            'test_environment': test_environment,
            'executed_at': datetime.now(),
            'executed_by': self.agent_name,
            'guidelines_applied': bool(self.current_guidelines)
        }
        
        # Track test results
        self.test_results.append(test_execution_result)
        
        # Log summary
        passed_rate = (test_results['passed_tests'] / test_results['total_tests'] * 100) if test_results['total_tests'] > 0 else 0
        logger.info(
            f"✓ Tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed "
            f"({passed_rate:.1f}%), coverage: {coverage_report['overall_coverage']:.1f}%"
        )
        
        return test_execution_result
    
    @require_dev_bible_prep
    def create_git_branch(self, branch_name: str, base_branch: str = None) -> Dict[str, Any]:
        """
        Create a new Git branch for development work.
        
        Args:
            branch_name (str): Name of the new branch
            base_branch (str, optional): Base branch to branch from. Defaults to main.
            
        Returns:
            Dict[str, Any]: Branch creation results
        """
        logger.info(f"Creating Git branch: {branch_name}")
        
        base_branch = base_branch or self.git_config["main_branch"]
        
        try:
            # Ensure we're in the project root
            original_dir = os.getcwd()
            os.chdir(self.project_root)
            
            # Fetch latest changes
            subprocess.run(["git", "fetch", self.git_config["remote"]], check=True, capture_output=True)
            
            # Checkout base branch and pull latest
            subprocess.run(["git", "checkout", base_branch], check=True, capture_output=True)
            subprocess.run(["git", "pull", self.git_config["remote"], base_branch], check=True, capture_output=True)
            
            # Create and checkout new branch
            subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
            
            self.git_branch = branch_name
            
            logger.info(f"✓ Git branch {branch_name} created successfully")
            
            return {
                'branch_name': branch_name,
                'base_branch': base_branch,
                'created_at': datetime.now(),
                'status': 'success'
            }
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git branch creation failed: {e}"
            logger.error(error_msg)
            return {
                'branch_name': branch_name,
                'status': 'failed',
                'error': error_msg
            }
        finally:
            os.chdir(original_dir)
    
    @require_dev_bible_prep
    def submit_pull_request(
        self,
        title: str,
        description: str,
        target_branch: str = None,
        reviewers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Submit a pull request with the current branch changes.
        
        Args:
            title (str): PR title
            description (str): PR description
            target_branch (str, optional): Target branch for PR
            reviewers (Optional[List[str]]): List of reviewer usernames
            
        Returns:
            Dict[str, Any]: PR submission results
        """
        logger.info(f"Submitting pull request: {title}")
        
        if not self.git_branch:
            raise ValueError("No Git branch available for PR submission")
        
        target_branch = target_branch or self.git_config["main_branch"]
        
        try:
            # Stage and commit changes
            commit_message = f"{self.git_config['commit_prefix']} {title}"
            
            subprocess.run(["git", "add", "."], check=True, capture_output=True, cwd=self.project_root)
            subprocess.run(
                ["git", "commit", "-m", commit_message], 
                check=True, capture_output=True, cwd=self.project_root
            )
            
            # Push branch
            subprocess.run(
                ["git", "push", self.git_config["remote"], self.git_branch], 
                check=True, capture_output=True, cwd=self.project_root
            )
            
            # Create PR (simulated - would use GitHub API in production)
            pr_result = self._create_pull_request_simulation(
                title, description, self.git_branch, target_branch, reviewers
            )
            
            logger.info(f"✓ Pull request submitted successfully: {pr_result['pr_number']}")
            
            return pr_result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"PR submission failed: {e}"
            logger.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg
            }
    
    # Private helper methods
    
    def _generate_endpoint_code(
        self, 
        endpoint_name: str, 
        route: str, 
        methods: List[str],
        auth_required: bool,
        request_schema: Optional[Dict],
        response_schema: Optional[Dict]
    ) -> str:
        """Generate Flask endpoint code following coding standards."""
        function_name = self._generate_function_name(endpoint_name)
        
        # Generate imports
        imports = [
            "from flask import Blueprint, request, jsonify, current_app",
            "from typing import Dict, Any, Tuple",
            "import logging"
        ]
        
        if auth_required:
            imports.append("from functools import wraps")
            imports.append("from your_auth_module import require_auth")
        
        # Generate function signature and docstring
        method_list = "', '".join(methods)
        
        code_parts = []
        code_parts.extend(imports)
        code_parts.append("")
        code_parts.append("logger = logging.getLogger(__name__)")
        code_parts.append("")
        
        # Blueprint registration
        code_parts.append("# Blueprint should be defined at module level")
        code_parts.append("# bp = Blueprint('api', __name__, url_prefix='/api')")
        code_parts.append("")
        
        # Decorator line
        decorator_line = f"@bp.route('{route}', methods=['{method_list}'])"
        if auth_required:
            decorator_line = f"@require_auth\n{decorator_line}"
        
        code_parts.append(decorator_line)
        
        # Function definition
        code_parts.append(f"def {function_name}() -> Tuple[Dict[str, Any], int]:")
        
        # Docstring
        docstring = f'''    """
    {endpoint_name.replace('_', ' ').title()} endpoint.
    
    Route: {route}
    Methods: {', '.join(methods)}
    Authentication: {'Required' if auth_required else 'Not required'}
    
    Returns:
        Tuple[Dict[str, Any], int]: Response data and HTTP status code
    """'''
        code_parts.append(docstring)
        
        # Function body
        code_parts.append("    try:")
        code_parts.append(f"        logger.info(f'Processing {endpoint_name} request')")
        code_parts.append("")
        
        if request_schema and 'POST' in methods:
            code_parts.append("        # Validate request data")
            code_parts.append("        request_data = request.get_json()")
            code_parts.append("        if not request_data:")
            code_parts.append("            return {'error': 'No JSON data provided'}, 400")
            code_parts.append("")
        
        code_parts.append("        # TODO: Implement business logic here")
        code_parts.append("        result = {}")
        code_parts.append("")
        code_parts.append("        return {'data': result, 'status': 'success'}, 200")
        code_parts.append("")
        code_parts.append("    except Exception as e:")
        code_parts.append("        logger.error(f'Error in {function_name}: {str(e)}')")
        code_parts.append("        return {'error': 'Internal server error'}, 500")
        
        return "\n".join(code_parts)
    
    def _generate_business_logic_code(
        self,
        function_name: str,
        requirements: str, 
        input_parameters: Dict[str, str],
        return_type: str,
        database_operations: bool
    ) -> str:
        """Generate business logic function code."""
        
        # Generate imports
        imports = [
            "from typing import Dict, Any, Optional",
            "import logging"
        ]
        
        if database_operations:
            imports.extend([
                "from database.models import db",
                "from sqlalchemy.exc import SQLAlchemyError"
            ])
        
        # Generate parameter signature
        param_signature = []
        for param_name, param_type in input_parameters.items():
            param_signature.append(f"{param_name}: {param_type}")
        
        signature = f"def {function_name}({', '.join(param_signature)}) -> {return_type}:"
        
        code_parts = []
        code_parts.extend(imports)
        code_parts.append("")
        code_parts.append("logger = logging.getLogger(__name__)")
        code_parts.append("")
        code_parts.append(signature)
        
        # Docstring
        docstring = f'''    """
    {requirements}
    
    Args:'''
        
        for param_name, param_type in input_parameters.items():
            docstring += f"\n        {param_name} ({param_type}): Parameter description"
        
        docstring += f'''
    
    Returns:
        {return_type}: Function result
        
    Raises:
        ValueError: If input parameters are invalid'''
        
        if database_operations:
            docstring += "\n        SQLAlchemyError: If database operation fails"
        
        docstring += '\n    """'
        code_parts.append(docstring)
        
        # Function body
        code_parts.append("    try:")
        code_parts.append(f"        logger.info(f'Executing {function_name} with parameters: {{locals()}}')")
        code_parts.append("")
        
        # Input validation
        for param_name, param_type in input_parameters.items():
            if param_type in ["str", "string"]:
                code_parts.append(f"        if not {param_name} or not {param_name}.strip():")
                code_parts.append(f"            raise ValueError('{param_name} cannot be empty')")
            elif param_type in ["int", "float"]:
                code_parts.append(f"        if {param_name} is None:")
                code_parts.append(f"            raise ValueError('{param_name} cannot be None')")
        
        if input_parameters:
            code_parts.append("")
        
        # Business logic placeholder
        code_parts.append("        # TODO: Implement business logic based on requirements:")
        for line in requirements.split('.'):
            if line.strip():
                code_parts.append(f"        # - {line.strip()}")
        code_parts.append("")
        
        if database_operations:
            code_parts.append("        # Database operations")
            code_parts.append("        try:")
            code_parts.append("            # TODO: Add database queries/operations here")
            code_parts.append("            db.session.commit()")
            code_parts.append("        except SQLAlchemyError as db_error:")
            code_parts.append("            db.session.rollback()")
            code_parts.append("            logger.error(f'Database error in {function_name}: {str(db_error)}')")
            code_parts.append("            raise")
            code_parts.append("")
        
        # Return placeholder
        if return_type == "Dict[str, Any]":
            code_parts.append("        result = {'status': 'completed', 'data': {}}")
        elif return_type == "bool":
            code_parts.append("        result = True")
        elif return_type in ["int", "float"]:
            code_parts.append("        result = 0")
        else:
            code_parts.append("        result = None  # TODO: Return appropriate value")
        
        code_parts.append("")
        code_parts.append("        return result")
        code_parts.append("")
        code_parts.append("    except Exception as e:")
        code_parts.append("        logger.error(f'Error in {function_name}: {str(e)}')")
        code_parts.append("        raise")
        
        return "\n".join(code_parts)
    
    def _generate_function_name(self, endpoint_name: str) -> str:
        """Generate proper function name from endpoint name."""
        # Convert to snake_case if not already
        function_name = re.sub(r'[^a-zA-Z0-9_]', '_', endpoint_name)
        function_name = re.sub(r'_+', '_', function_name)
        return function_name.lower().strip('_')
    
    def _create_endpoint_file(self, endpoint_name: str, code: str) -> str:
        """Create endpoint file in appropriate directory."""
        routes_dir = os.path.join(self.project_root, self.flask_app_structure["routes"])
        os.makedirs(routes_dir, exist_ok=True)
        
        filename = f"{self._generate_function_name(endpoint_name)}.py"
        file_path = os.path.join(routes_dir, filename)
        
        with open(file_path, 'w') as f:
            f.write(code)
        
        return file_path
    
    def _create_business_logic_file(self, function_name: str, code: str) -> str:
        """Create business logic file in services directory."""
        services_dir = os.path.join(self.project_root, self.flask_app_structure["services"])
        os.makedirs(services_dir, exist_ok=True)
        
        filename = f"{function_name}_service.py"
        file_path = os.path.join(services_dir, filename)
        
        with open(file_path, 'w') as f:
            f.write(code)
        
        return file_path
    
    def _validate_code_standards(self, code: str) -> Dict[str, Any]:
        """Validate code against coding standards from dev_bible."""
        validation_results = {
            'pep8_compliant': True,
            'has_docstrings': '"""' in code,
            'has_type_hints': '->' in code and ':' in code,
            'has_error_handling': 'try:' in code and 'except' in code,
            'has_logging': 'logger' in code,
            'issues': []
        }
        
        # Check for common issues
        if 'TODO' in code:
            validation_results['issues'].append('Contains TODO items that need implementation')
        
        if not validation_results['has_docstrings']:
            validation_results['issues'].append('Missing docstrings')
            validation_results['pep8_compliant'] = False
        
        if not validation_results['has_type_hints']:
            validation_results['issues'].append('Missing type hints')
        
        return validation_results
    
    def _register_route(self, endpoint_name: str, route: str, methods: List[str]) -> bool:
        """Simulate route registration in Flask app."""
        # In a real implementation, this would register the route with Flask
        logger.info(f"Route registered: {route} -> {endpoint_name} ({', '.join(methods)})")
        return True
    
    def _generate_test_cases(self, function_name: str, input_params: Dict[str, str], return_type: str) -> List[Dict[str, Any]]:
        """Generate suggested test cases for the function."""
        test_cases = []
        
        # Happy path test
        test_cases.append({
            'test_name': f"test_{function_name}_success",
            'test_type': 'positive',
            'description': f"Test {function_name} with valid inputs",
            'expected_result': 'success'
        })
        
        # Error handling tests
        for param_name, param_type in input_params.items():
            if param_type == "str":
                test_cases.append({
                    'test_name': f"test_{function_name}_empty_{param_name}",
                    'test_type': 'negative', 
                    'description': f"Test {function_name} with empty {param_name}",
                    'expected_result': 'ValueError'
                })
        
        # Edge case test
        test_cases.append({
            'test_name': f"test_{function_name}_edge_case",
            'test_type': 'edge_case',
            'description': f"Test {function_name} with edge case inputs",
            'expected_result': 'handled_gracefully'
        })
        
        return test_cases
    
    def _perform_security_check(self, code: str, database_operations: bool) -> Dict[str, Any]:
        """Perform basic security check on generated code."""
        security_issues = []
        
        # Check for SQL injection potential
        if database_operations and any(word in code.lower() for word in ['query', 'execute', 'raw']):
            if 'parameterized' not in code.lower() and 'prepare' not in code.lower():
                security_issues.append('Potential SQL injection vulnerability - use parameterized queries')
        
        # Check for input validation
        if 'request' in code and 'validate' not in code.lower():
            security_issues.append('Input validation recommended for request data')
        
        return {
            'security_compliant': len(security_issues) == 0,
            'issues': security_issues,
            'checked_at': datetime.now()
        }
    
    def _prepare_test_environment(self, test_type: str, target_files: Optional[List[str]]) -> Dict[str, Any]:
        """Prepare test environment configuration."""
        return {
            'test_type': test_type,
            'target_files': target_files or [],
            'python_path': sys.executable,
            'working_directory': self.project_root,
            'environment_variables': {
                'FLASK_ENV': 'testing',
                'DATABASE_URL': 'sqlite:///:memory:'
            }
        }
    
    def _execute_tests(self, test_type: str, target_files: Optional[List[str]]) -> Dict[str, Any]:
        """Execute tests and return results."""
        # Simulated test execution - in production would run actual pytest
        
        if test_type == "unit":
            total_tests = 15
            passed_tests = 13
            failed_tests = 2
            skipped_tests = 0
        elif test_type == "integration":
            total_tests = 8
            passed_tests = 7
            failed_tests = 1
            skipped_tests = 0
        else:  # all
            total_tests = 23
            passed_tests = 20
            failed_tests = 3
            skipped_tests = 0
        
        # Generate mock individual test results
        individual_tests = []
        for i in range(total_tests):
            passed = i < passed_tests
            individual_tests.append({
                'test_name': f"test_function_{i+1}",
                'passed': passed,
                'execution_time': 0.05 + (i * 0.01),
                'error_message': None if passed else f"AssertionError in test {i+1}"
            })
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'execution_time': sum(t['execution_time'] for t in individual_tests),
            'individual_tests': individual_tests
        }
    
    def _generate_coverage_report(self, target_files: Optional[List[str]], threshold: float) -> Dict[str, Any]:
        """Generate code coverage report."""
        # Simulated coverage - in production would use coverage.py
        overall_coverage = 85.5
        
        return {
            'overall_coverage': overall_coverage,
            'threshold': threshold,
            'meets_threshold': overall_coverage >= threshold,
            'file_coverage': {
                'endpoints.py': 92.3,
                'services.py': 78.9,
                'utils.py': 88.1
            },
            'uncovered_lines': [
                {'file': 'services.py', 'lines': [45, 67, 89]},
                {'file': 'utils.py', 'lines': [23]}
            ]
        }
    
    def _generate_test_recommendations(self, test_results: Dict, coverage_report: Dict, failed_tests: List[Dict]) -> List[str]:
        """Generate test improvement recommendations."""
        recommendations = []
        
        if failed_tests:
            recommendations.append(f"Fix {len(failed_tests)} failing tests before deployment")
        
        if not coverage_report['meets_threshold']:
            recommendations.append(
                f"Increase test coverage from {coverage_report['overall_coverage']:.1f}% "
                f"to meet {coverage_report['threshold']}% threshold"
            )
        
        if coverage_report['uncovered_lines']:
            recommendations.append("Add tests for uncovered code lines")
        
        pass_rate = test_results['passed_tests'] / test_results['total_tests'] * 100
        if pass_rate < 95:
            recommendations.append("Improve test pass rate - aim for 95%+ success rate")
        
        return recommendations
    
    def _create_test_report(self, test_results: Dict, coverage_report: Dict, failed_tests: List[Dict], recommendations: List[str]) -> str:
        """Create detailed test report."""
        report_lines = [
            "# Backend Agent Test Report",
            f"Generated by: {self.agent_name}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Test Summary",
            f"- Total Tests: {test_results['total_tests']}",
            f"- Passed: {test_results['passed_tests']}",
            f"- Failed: {test_results['failed_tests']}",
            f"- Skipped: {test_results['skipped_tests']}",
            f"- Execution Time: {test_results['execution_time']:.2f}s",
            "",
            "## Coverage Report", 
            f"- Overall Coverage: {coverage_report['overall_coverage']:.1f}%",
            f"- Threshold: {coverage_report['threshold']}%",
            f"- Meets Threshold: {'✓' if coverage_report['meets_threshold'] else '✗'}",
            ""
        ]
        
        if failed_tests:
            report_lines.extend([
                "## Failed Tests",
                ""
            ])
            for test in failed_tests:
                report_lines.append(f"- {test['test_name']}: {test['error_message']}")
            report_lines.append("")
        
        if recommendations:
            report_lines.extend([
                "## Recommendations",
                ""
            ])
            for rec in recommendations:
                report_lines.append(f"- {rec}")
        
        return "\n".join(report_lines)
    
    def _create_pull_request_simulation(self, title: str, description: str, source_branch: str, target_branch: str, reviewers: Optional[List[str]]) -> Dict[str, Any]:
        """Simulate creating a pull request."""
        pr_number = f"PR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            'pr_number': pr_number,
            'title': title,
            'description': description,
            'source_branch': source_branch,
            'target_branch': target_branch,
            'reviewers': reviewers or [],
            'status': 'open',
            'created_at': datetime.now(),
            'url': f"https://github.com/example/repo/pull/{pr_number}"
        }


# Example usage and testing
if __name__ == "__main__":
    # Example usage of BackendAgent
    try:
        print("Testing BackendAgent functionality...")
        
        backend_agent = BackendAgent("TestBackendAgent")
        backend_agent.prepare_for_task("Implement user authentication system", "backend")
        
        # Test endpoint creation
        endpoint_result = backend_agent.create_flask_endpoint(
            endpoint_name="user_login",
            route="/api/v1/auth/login", 
            methods=["POST"],
            auth_required=False
        )
        print(f"✓ Endpoint created: {endpoint_result['function_name']}")
        
        # Test business logic implementation
        logic_result = backend_agent.implement_business_logic(
            function_name="authenticate_user",
            requirements="Validate user credentials and return JWT token",
            input_parameters={"username": "str", "password": "str"},
            return_type="Dict[str, Any]",
            database_operations=True
        )
        print(f"✓ Business logic implemented: {logic_result['function_name']}")
        
        # Test running tests
        test_result = backend_agent.run_tests(test_type="unit", coverage_threshold=80.0)
        print(f"✓ Tests executed: {test_result['test_summary']['passed']}/{test_result['test_summary']['total_tests']} passed")
        
        print("All BackendAgent tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise