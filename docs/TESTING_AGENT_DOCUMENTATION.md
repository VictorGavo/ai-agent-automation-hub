# 🧪 Testing Agent Documentation

## Overview

The Testing Agent is an automated testing system that monitors pull requests, runs comprehensive test suites, and reports results to Discord. It complements the Backend Agent by providing quality assurance and automated validation of code changes.

## 🚀 Key Features

### Automated Testing
- **PR Monitoring**: Automatically detects new PRs from agents
- **Comprehensive Test Suites**: Runs unit tests, security scans, code quality checks
- **Multiple Test Types**: pytest, bandit security scans, flake8/black style checks
- **Integration Testing**: Supports integration and performance tests
- **Code Coverage**: Generates detailed coverage reports

### Discord Integration
- **Real-time Notifications**: Test results sent to Discord channels
- **Interactive Commands**: Manual test triggering and configuration
- **Mobile-Friendly**: Full mobile workflow support
- **Status Monitoring**: Live testing agent status and metrics

### Quality Assurance
- **Security Scanning**: Identifies security vulnerabilities with bandit
- **Code Style**: Enforces consistent code formatting
- **Coverage Analysis**: Tracks test coverage metrics
- **Performance Testing**: Optional benchmark support

### Automation
- **Auto-Approval**: Automatically approve PRs that pass all tests
- **Configurable**: Adjust polling intervals and approval settings
- **Docker Support**: Containerized deployment with health checks

## 📁 Architecture

```
agents/testing/
├── __init__.py          # Module initialization
├── main.py             # Entry point for testing agent
├── testing_agent.py    # Main testing agent class
├── test_runner.py      # Test execution engine
└── Dockerfile          # Docker configuration
```

### Core Components

#### TestingAgent (`testing_agent.py`)
- Monitors PRs for new commits
- Coordinates test execution
- Manages Discord notifications
- Handles auto-approval logic

#### TestRunner (`test_runner.py`)
- Executes comprehensive test suites
- Runs security scans and code quality checks
- Generates coverage reports
- Parses and formats test results

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TESTING_POLLING_INTERVAL` | PR check frequency (seconds) | 60 | No |
| `TESTING_AUTO_APPROVE` | Auto-approve passing PRs | true | No |
| `GITHUB_TOKEN` | GitHub API access | - | Yes |
| `DISCORD_BOT_TOKEN` | Discord bot token | - | Yes |
| `DATABASE_URL` | Database connection | - | Yes |

### Docker Configuration

The Testing Agent is configured in `docker-compose.yml`:

```yaml
testing-agent:
  build:
    context: .
    dockerfile: agents/testing/Dockerfile
  environment:
    - TESTING_POLLING_INTERVAL=60
    - TESTING_AUTO_APPROVE=true
    - GITHUB_TOKEN=${GITHUB_TOKEN}
    - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
  volumes:
    - .:/app:rw
    - ./logs:/app/logs
    - /tmp/testing_workspace:/tmp/testing_workspace
```

## 💬 Discord Commands

### `/test-pr <pr_number>`
Manually trigger tests on a specific pull request.

**Usage:**
```
/test-pr 42
```

**Response:**
- 🧪 Test execution confirmation
- Real-time status updates
- Complete results when finished

### `/test-status`
Get current testing agent status and recent test results.

**Response:**
- Agent online/offline status
- Number of active tests
- Auto-approval setting
- Recent test summary
- Performance statistics

### `/test-config [auto_approve] [polling_interval]`
Configure testing agent settings.

**Parameters:**
- `auto_approve`: Enable/disable automatic PR approval
- `polling_interval`: Set PR check frequency in seconds

**Example:**
```
/test-config auto_approve:Enable polling_interval:30
```

### `/test-logs [lines] [level]`
Retrieve recent testing agent logs.

**Parameters:**
- `lines`: Number of log lines (1-100, default: 20)
- `level`: Log level filter (all/error/warning/info)

## 🧪 Test Categories

### Unit Tests
- **Tool**: pytest
- **Scope**: All test files matching patterns
- **Coverage**: Integrated coverage reporting
- **Timeout**: 5 minutes

### Security Scanning
- **Tool**: bandit
- **Scope**: All Python files
- **Output**: JSON format with severity levels
- **Thresholds**: High severity issues cause failure

### Code Style
- **Tools**: flake8, black
- **Scope**: All Python files
- **Checks**: Syntax errors, formatting compliance
- **Standards**: PEP 8 compliance

### Integration Tests
- **Pattern**: Files/directories with "integration" in name
- **Timeout**: 10 minutes
- **Support**: pytest markers and directory structure

### Performance Tests
- **Tool**: pytest-benchmark (optional)
- **Scope**: Performance test files
- **Output**: Benchmark results and comparisons

## 📊 Test Results Format

### Discord Notification
```
🧪 Test Results - PR #42
✅ Status: PASS

📋 PR: Add user authentication feature
👤 Author: backend-agent
🌿 Branch: feature/auth

📊 Test Summary:
✅ Unit Tests: pass (95% coverage)
✅ Security Scan: pass (0 issues)
✅ Code Style: pass (compliant)
✅ Integration Tests: pass (5 tests)
⏭️ Performance: skip (no tests)

📈 Coverage: 95.2%
⏱️ Duration: 45.3s
```

### JSON Result Structure
```json
{
  "timestamp": "2025-09-23T10:30:00Z",
  "overall_status": "pass",
  "duration": 45.3,
  "categories": {
    "unit_tests": {
      "status": "pass",
      "tests_run": 24,
      "failures": 0,
      "errors": 0
    },
    "security_scan": {
      "status": "pass",
      "total_issues": 0,
      "high_issues": 0
    }
  },
  "coverage": {
    "percentage": 95.2,
    "lines_covered": 1832,
    "lines_total": 1925
  }
}
```

## 🔄 Workflow Integration

### Automatic Flow
1. **PR Detection**: Agent monitors for new commits
2. **Test Execution**: Comprehensive test suite runs
3. **Result Analysis**: Pass/fail determination
4. **Discord Notification**: Results sent to team
5. **Auto-Approval**: Passing PRs approved automatically (if enabled)

### Manual Flow
1. **Manual Trigger**: `/test-pr 42` command
2. **Test Execution**: Same comprehensive suite
3. **Result Notification**: Results sent to requester
4. **Manual Decision**: Human review if needed

## 🚀 Deployment

### Build and Run
```bash
# Build the testing agent
docker-compose build testing-agent

# Run the testing agent
docker-compose up testing-agent

# View logs
docker-compose logs -f testing-agent
```

### Validation
```bash
# Validate installation
python scripts/validate_testing_agent.py

# Run demo
python examples/testing_agent_demo.py
```

## 🔍 Monitoring

### Health Checks
- **Docker Health**: Automatic container health monitoring
- **Agent Status**: Periodic status reports to Discord
- **Error Handling**: Graceful failure recovery

### Logging
- **File Location**: `/app/logs/testing_agent.log`
- **Levels**: INFO, WARNING, ERROR, DEBUG
- **Rotation**: Automatic log rotation
- **Discord Access**: View logs via `/test-logs` command

### Metrics
- **Test Success Rate**: Percentage of passing tests
- **Execution Time**: Average test duration
- **Coverage Trends**: Code coverage over time
- **Auto-Approval Rate**: Automatic approval statistics

## 🔧 Troubleshooting

### Common Issues

#### Tests Not Running
- Check GitHub token permissions
- Verify PR detection patterns
- Review agent logs for errors

#### Security Scan Failures
- Update bandit rules if needed
- Review security issues in code
- Adjust severity thresholds

#### Coverage Issues
- Ensure pytest-cov is installed
- Check test file patterns
- Verify coverage configuration

#### Docker Issues
- Check container resource limits
- Verify volume mounts
- Review Docker logs

### Debug Commands
```bash
# Check agent status
docker-compose exec testing-agent python -c "
from agents.testing.testing_agent import TestingAgent
import asyncio
agent = TestingAgent()
print(asyncio.run(agent.get_status()))
"

# Manual test run
docker-compose exec testing-agent python -c "
from agents.testing.test_runner import TestRunner
import asyncio
runner = TestRunner()
# Add test workspace path
"
```

## 🎯 Best Practices

### Test Organization
- Use clear test file naming conventions
- Organize tests by feature/module
- Include integration tests for critical paths
- Maintain good test coverage (>80%)

### Security
- Regular security scan updates
- Review security issues promptly
- Use least-privilege principles
- Rotate tokens regularly

### Performance
- Monitor test execution times
- Optimize slow tests
- Use parallel execution where possible
- Cache dependencies appropriately

## 🔮 Future Enhancements

### Planned Features
- **Multi-language Support**: Support for Node.js, Go, etc.
- **Advanced Metrics**: Trend analysis and reporting
- **Custom Test Suites**: Project-specific test configurations
- **Parallel Testing**: Faster execution with parallel runners
- **Test History**: Historical test result tracking

### Integration Opportunities
- **CI/CD Integration**: GitHub Actions workflow integration
- **Code Quality Gates**: Automated quality gates
- **Deployment Testing**: Post-deployment verification
- **Performance Monitoring**: Continuous performance tracking

---

The Testing Agent provides comprehensive automated testing capabilities that ensure code quality and reliability while maintaining the fast, mobile-friendly development workflow established by the AI Agent Automation Hub.