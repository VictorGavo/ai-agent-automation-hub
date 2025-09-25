# 👀 Testing Agent Monitoring Guide

## How to Know Your Testing Agent is Active & Running

When you run the Testing Agent, you'll have **multiple ways** to monitor its activity and confirm it's working properly:

## 🚀 1. Startup Notifications (Discord)

When the Testing Agent starts, you'll receive a Discord notification like this:

```
🧪 Testing Agent Started!

✅ Status: Online and monitoring
🔄 Monitoring: Checking PRs every 60s  
🤖 Auto-Approve: Enabled
📁 Workspace: /tmp/testing_workspace

Ready to test PRs automatically! Use /test-status for details.
```

## 📊 2. Enhanced /status Command (Discord)

The main `/status` command now includes Testing Agent information:

```
🤖 Automation Hub Status

🔧 System                    📋 Active Tasks              🔄 Pull Requests
Status: Running              Total: 5                     Open PRs: 3
Uptime: 2h 15m              Pending: 1                   Awaiting Approval: 2
GitHub: ✅                  In Progress: 2               Recent Activity: 1 merged

🧪 Testing Agent             📊 Agent Performance         🐙 GitHub Integration
Status: 🟢 Online           Success Rate: 94.2%          Repository: ai-agent-automation-hub
Active Tests: 1             Tasks/Day: 12                Operations: 15 commits, 8 PRs  
Auto-Approve: ✅ On         Avg Response: 1.2s           Success Rate: 96.7%
Test Success: 91.3% (23 total)  Errors: 0

💡 /test-status • /pending-prs • /assign-task • /review [pr-number] • /approve [pr-number]
```

## 🧪 3. Dedicated /test-status Command

Get detailed Testing Agent status:

```
🧪 Testing Agent Status

Agent Status: 🟢 Online            Active Tests: 0 running         Auto-Approve: ✅ Enabled

Recent Tests (Last 5):
PR #42: pass (45.1s)
PR #41: pass (32.8s)  
PR #40: fail (28.3s)
PR #39: pass (41.2s)
PR #38: pass (38.9s)

Test Statistics:
Total: 156 | Passed: 142 | Failed: 14
```

## 🔄 4. Real-Time Activity Notifications

You'll see notifications when tests start and complete:

**Test Starting:**
```
🧪 Starting Tests - PR #43

📋 PR: Add user authentication system
👤 Author: backend-agent
🌿 Branch: feature/auth-system

🔄 Running comprehensive test suite...
⏱️ Expected duration: ~1-2 minutes
```

**Test Completed:**
```
🧪 Test Results - PR #43
✅ Status: PASS

📋 PR: Add user authentication system
👤 Author: backend-agent
🌿 Branch: feature/auth-system

📊 Test Summary:
✅ Unit Tests: pass (95% coverage)
✅ Security Scan: pass (0 issues)
✅ Code Style: pass (compliant)
✅ Integration: pass (8 tests)

📈 Coverage: 95.2% | ⏱️ Duration: 45.3s
🤖 Auto-Approved - Ready for merge!
```

## 🐳 5. Docker Health Checks

The Testing Agent has built-in health monitoring:

```bash
# Check if container is healthy
docker ps | grep testing-agent

# View health check endpoint
curl http://localhost:8083/health

# Response:
{
  "status": "healthy",
  "agent": "testing-agent", 
  "online": true,
  "active_tests": 0,
  "auto_approve": true,
  "workspace": "/tmp/testing_workspace",
  "uptime": "running"
}
```

## 📈 6. Real-Time Monitoring Script

Use the dedicated monitoring tool:

```bash
# Start real-time monitoring
python scripts/monitor_testing_agent.py

# Output:
🧪 Testing Agent Monitor Started
============================================================
Monitoring: http://localhost:8083
Started: 2025-09-24 15:30:15

[15:30:15] 🟢 Testing Agent Online
[15:30:15] 📊 Status: Tests: 0 | Auto-approve: On
[15:32:30] 🧪 New test started (Total: 1)
[15:34:45] ✅ Test completed (Remaining: 0)
[15:35:15] 📊 Status: Tests: 0 | Auto-approve: On
```

## 🔍 7. Quick Status Checker

Run a comprehensive status check:

```bash
# Quick status check
python scripts/check_testing_agent.py

# Output:
🧪 Testing Agent Status Report
==================================================
Checked: 2025-09-24 15:30:45

🐳 Docker Container:
   ✅ Running - automation_hub_testing_agent   Up 2 hours

💚 Health Check (http://localhost:8083/health):
   ✅ Healthy
   📊 Active Tests: 0
   🤖 Auto-Approve: true
   📁 Workspace: /tmp/testing_workspace

📊 Detailed Status:
   ✅ Agent: testing-agent
   🔄 Status: running
   🧪 Active Tests: 0
   📈 Tested Commits: 15
   🤖 Auto-Approve: true
   ⏱️ Polling Interval: 60s
   📁 Workspace: /tmp/testing_workspace

🎯 Overall Status:
   ✅ Testing Agent is RUNNING and HEALTHY
   🚀 Ready to test PRs automatically!

💡 Quick Commands:
   /test-status    - Check from Discord
   /test-pr 42     - Test specific PR  
   /test-config    - Adjust settings
```

## 🔊 8. Log Monitoring

View detailed logs:

```bash
# View Testing Agent logs
docker-compose logs -f testing-agent

# Or via Discord
/test-logs lines:50 level:info

# Sample log output:
2025-09-24 15:30:15 - INFO - Testing Agent started
2025-09-24 15:30:15 - INFO - Health check server started on port 8083
2025-09-24 15:30:16 - INFO - Testing Agent monitoring pulse - Cycle 1 | Active tests: 0 | Tested commits: 0
2025-09-24 15:32:30 - INFO - 🧪 Detected new agent PR #43 - 'Add user authentication system' by backend-agent
2025-09-24 15:32:31 - INFO - Running tests for PR #43 - Add user authentication system
2025-09-24 15:34:45 - INFO - Tests completed for PR #43: PASS (135.2s)
```

## 🎯 Quick Activity Verification

To quickly verify the Testing Agent is active:

### From Discord (Mobile-Friendly):
1. Type `/status` - See Testing Agent in the status dashboard
2. Type `/test-status` - Get detailed testing information
3. Look for startup notification when agent starts

### From Terminal:
1. `python scripts/check_testing_agent.py` - Comprehensive status
2. `docker-compose logs testing-agent` - View logs
3. `curl http://localhost:8083/health` - Quick health check

### Automatic Indicators:
- 🟢 Status shows "Online" in Discord `/status`
- 🧪 Notifications appear when PRs are tested
- 📊 Active test counts update in real-time
- ✅ Test results appear automatically

## 🔄 Activity Flow You'll See

When everything is working, here's what you'll observe:

1. **Startup** → Discord notification "Testing Agent Started!"
2. **Monitoring** → Periodic log messages showing monitoring cycles  
3. **PR Detection** → "Detected new agent PR #X" in logs
4. **Test Start** → "Starting Tests - PR #X" Discord notification
5. **Test Progress** → Log messages showing test execution
6. **Test Complete** → "Test Results - PR #X" with full details
7. **Auto-Approval** → "Auto-Approved PR #X" if tests pass

You'll always know your Testing Agent is active and working! 🚀