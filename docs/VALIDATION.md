# Deployment Validation Guide

## Overview

The `validate_deployment.py` script provides comprehensive validation of your AI Agent Automation Hub deployment. It tests all major components, runs end-to-end workflows, performs health checks, and generates detailed reports with recommendations.

## Features

### 🔍 Component Testing
- **DevBibleReader**: Validates documentation loading and access
- **BaseAgent & Specialized Agents**: Tests agent initialization and functionality
- **Discord Bot**: Verifies bot configuration and connectivity
- **PostgreSQL Database**: Tests connection and operations
- **Docker Containers**: Checks container status and configuration

### 🔄 End-to-End Workflow Testing
- Simulates complete task assignment workflow
- Tests orchestrator agent coordination
- Validates agent selection logic
- Verifies dev bible context preparation
- Tests task execution and status reporting

### 🏥 Health Monitoring
- **System Resources**: CPU, memory, disk usage on Pi 5
- **Environment Variables**: Required configuration validation
- **File Permissions**: Directory structure and access rights
- **Network Connectivity**: External service accessibility
- **Log Management**: File rotation and disk space monitoring

### 📊 Comprehensive Reporting
- Component status with ✅/❌/⚠️ indicators
- Performance metrics and resource usage
- Configuration validation results
- Actionable recommendations for issues
- Production readiness assessment

## Usage

### Basic Validation

```bash
# Run all validation tests
python scripts/validate_deployment.py

# Using make command
make validate-deployment

# Using installed console script
automation-hub-validate
```

### Advanced Options

```bash
# Verbose output with detailed logging
python scripts/validate_deployment.py --verbose

# JSON output for automation/CI
python scripts/validate_deployment.py --json

# Save report to file
python scripts/validate_deployment.py --output deployment_report.txt

# Custom configuration file
python scripts/validate_deployment.py --config custom.env
```

### Make Commands

```bash
# Standard validation
make validate-deployment

# JSON output for CI/CD
make validate-deployment-json
```

## Test Categories

### 1. Environment & Configuration Tests

**Environment Variables**
- Tests for required variables (DISCORD_TOKEN, DATABASE_URL, APP_MODE)
- Validates optional configuration
- Reports missing or invalid settings

**File Structure**
- Verifies all required files and directories exist
- Checks file permissions and accessibility
- Validates project structure integrity

### 2. Database Tests

**Connection Test**
- Tests PostgreSQL connectivity
- Validates connection parameters
- Reports connection failures with details

**Operations Test**
- Verifies table existence (tasks, agents, logs)
- Tests basic CRUD operations
- Validates database schema integrity

### 3. Component Tests

**DevBibleReader**
- Tests documentation loading functionality
- Validates required documentation sections
- Reports missing or inaccessible content

**Agent Systems**
- Tests BaseAgent initialization
- Validates specialized agent creation (Backend, Testing, Orchestrator)
- Verifies agent communication interfaces

**Discord Bot Configuration**
- Tests bot configuration loading
- Validates Discord token and settings
- Reports configuration issues

### 4. End-to-End Workflow

**Complete Task Simulation**
- Creates mock task assignment
- Tests orchestrator coordination
- Validates agent selection logic
- Verifies task execution pipeline

### 5. System Health Checks

**Resource Monitoring**
- CPU usage analysis (warns >75%, fails >90%)
- Memory usage tracking (warns >80%, fails >90%)  
- Disk space monitoring (warns >85%, fails >95%)
- Load average assessment (Pi-specific)

**Log File Management**
- Tests log directory accessibility
- Checks file permissions and rotation
- Monitors disk space usage
- Validates log file sizes

**Network Connectivity**
- Tests Discord API accessibility
- Validates external service connections
- Checks database connectivity (if remote)
- Reports network-related issues

### 6. Docker Integration

**Container Status**
- Lists running containers
- Validates expected services (discord-bot, postgres)
- Reports container health and configuration

## Sample Output

### Successful Validation

```
================================================================================
🤖 AI AGENT AUTOMATION HUB - DEPLOYMENT VALIDATION REPORT
================================================================================

🟢 OVERALL STATUS: ✅ DEPLOYMENT VALIDATION PASSED

📊 SUMMARY:
   • Total Tests: 12
   • Passed: 12
   • Failed: 0
   • Warnings: 0
   • Skipped: 0
   • Execution Time: 3.45 seconds

🖥️ SYSTEM INFORMATION:
   • Platform: Raspberry Pi
   • CPU Usage: 23.1%
   • Memory Usage: 45.2%
   • Disk Usage: 28.7%
   • Load Average: 0.85, 0.92, 1.02
   • Uptime: 2 days, 14:23:15

================================================================================
📋 DETAILED TEST RESULTS:
================================================================================

🔧 ENVIRONMENT:
────────────────────────────────────────
   ✅ Required Environment Variables: All environment variables present
   ⏱️ Execution time: 0.02s
   ✅ File Structure: All required files and directories present with correct permissions
   ⏱️ Execution time: 0.15s

🔧 DATABASE:
────────────────────────────────────────
   ✅ Connection: Database connection successful
   ⏱️ Execution time: 0.23s
   ✅ Operations: Database operations working correctly
   ⏱️ Execution time: 0.18s

🔧 DEVBIBLE:
────────────────────────────────────────
   ✅ Reader: DevBibleReader loaded 8 documentation files successfully
   ⏱️ Execution time: 0.12s

🔧 AGENTS:
────────────────────────────────────────
   ✅ BaseAgent: BaseAgent initialization successful
   ⏱️ Execution time: 0.08s
   ✅ Specialized Agents: All specialized agents initialized successfully: BackendAgent, TestingAgent, Orchestrator
   ⏱️ Execution time: 0.19s

🔧 DISCORD BOT:
────────────────────────────────────────
   ✅ Configuration: Discord bot configuration valid
   ⏱️ Execution time: 0.11s

🔧 E2E WORKFLOW:
────────────────────────────────────────
   ✅ Complete Workflow: End-to-end workflow simulation successful
   ⏱️ Execution time: 0.25s

🔧 SYSTEM HEALTH:
────────────────────────────────────────
   ✅ Resource Usage: System resources within normal limits
   ⏱️ Execution time: 1.02s
   ✅ Log Files: Log files healthy (4 files, 12.3MB total)
   ⏱️ Execution time: 0.08s
   ✅ Network Connectivity: All network connectivity tests passed
   ⏱️ Execution time: 1.15s

🔧 DOCKER:
────────────────────────────────────────
   ✅ Container Status: Docker containers running (3 active)
   ⏱️ Execution time: 0.27s

================================================================================
🚀 NEXT STEPS:
================================================================================

✅ DEPLOYMENT READY FOR PRODUCTION!

Your AI Agent Automation Hub deployment has passed all validation tests.
You can proceed with confidence to production deployment.

Recommended next steps:
1. Set up monitoring and alerting
2. Configure automated backups
3. Set up log rotation
4. Review security configurations
5. Test with real Discord server and users
```

### Validation with Warnings

```
🟡 OVERALL STATUS: ⚠️ DEPLOYMENT VALIDATION PASSED WITH WARNINGS

⚠️ WARNINGS TO ADDRESS:
   • Environment - Environment Variables: Missing optional variables: ENCRYPTION_KEY, PROMETHEUS_ENABLED
   • DevBible - Reader: Missing documentation sections: security_rules
   • System Health - Resource Usage: Elevated memory usage: 83.2%
   • Docker - Container Status: Expected containers not running: prometheus

Priority actions:
1. Address the warning items listed above
2. Set up monitoring for the flagged components
3. Test thoroughly in a staging environment
4. Proceed with cautious production deployment
```

### Failed Validation

```
🔴 OVERALL STATUS: ❌ DEPLOYMENT VALIDATION FAILED

🚨 CRITICAL ISSUES TO RESOLVE:
   • Environment - Required Environment Variables: Missing required variables: DISCORD_TOKEN
   • Database - Connection: Database connection failed: connection refused
   • Agents - Specialized Agents: Failed: TestingAgent (import failed). Successful: BackendAgent, Orchestrator

Required actions:
1. Fix all failed tests listed above
2. Address warning items  
3. Re-run validation after fixes
4. Consider testing in a development environment first
```

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Run Deployment Validation
  run: |
    python scripts/validate_deployment.py --json --output validation_results.json
  env:
    DISCORD_TOKEN: ${{ secrets.DISCORD_TOKEN }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}

- name: Upload Validation Results
  uses: actions/upload-artifact@v3
  with:
    name: validation-results
    path: validation_results.json
```

### Docker Health Checks

```yaml
healthcheck:
  test: ["CMD", "python", "scripts/validate_deployment.py", "--json"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Troubleshooting

### Common Issues

**Environment Variables Missing**
```bash
# Check current environment
env | grep -E "(DISCORD|DATABASE|APP_MODE)"

# Source your .env file
source .env

# Verify settings
python -c "import os; print('DISCORD_TOKEN:', bool(os.getenv('DISCORD_TOKEN')))"
```

**Database Connection Failed**
```bash
# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"

# Check if PostgreSQL is running
systemctl status postgresql
# or for Docker
docker-compose ps postgres
```

**Missing Files or Permissions**
```bash
# Check file structure
find . -name "*.py" -type f ! -executable -ls

# Fix permissions
chmod +r agents/**/*.py
chmod +x scripts/*.py
```

**Import Errors**
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Install missing dependencies
pip install -e .[dev,all]
```

### Performance Issues

**High Resource Usage**
- Check for memory leaks in long-running processes
- Monitor CPU usage during validation
- Consider reducing concurrent task limits

**Slow Network Tests**
- Check internet connectivity
- Verify DNS resolution
- Test individual endpoints manually

## Customization

### Adding Custom Tests

```python
@_time_test
async def test_custom_component(self) -> ValidationResult:
    """Test your custom component."""
    try:
        # Your test logic here
        return ValidationResult(
            component="Custom",
            test_name="Custom Test",
            result=TestResult.PASS,
            message="Custom component working correctly"
        )
    except Exception as e:
        return ValidationResult(
            component="Custom",
            test_name="Custom Test", 
            result=TestResult.FAIL,
            message=f"Custom test failed: {str(e)}"
        )

# Add to run_all_tests method:
self.add_result(await self.test_custom_component())
```

### Custom Thresholds

```python
# Modify resource thresholds in test_system_resources
if metrics.cpu_usage > 95:  # Custom CPU threshold
    errors.append(f"Critical CPU usage: {metrics.cpu_usage}%")
```

## Best Practices

### Pre-Production Checklist

1. **Run validation in development environment first**
2. **Address all failed tests before production**
3. **Consider warnings as potential production issues**
4. **Test with actual Discord server configuration**
5. **Verify database migrations and schema**
6. **Test with realistic data volumes**
7. **Validate backup and recovery procedures**

### Regular Monitoring

- Run validation after major deployments
- Include in CI/CD pipeline
- Monitor resource trends over time
- Set up alerting for validation failures
- Regular security and dependency updates

### Documentation

- Keep validation results for compliance
- Document any custom modifications
- Maintain environment variable documentation
- Update validation tests for new components

---

For more information, see the main [DEPLOYMENT.md](../DEPLOYMENT.md) guide.