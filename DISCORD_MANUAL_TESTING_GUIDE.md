# Discord Bot Manual Testing Guide

This guide provides step-by-step instructions for manually testing the Discord bot integration to complement the automated test suite.

## 🎯 Pre-Test Checklist

- [ ] Discord bot is running (`python bot/run_bot.py`)
- [ ] Bot appears online in your Discord server
- [ ] You have appropriate permissions in the server
- [ ] Both mobile and desktop Discord apps available for testing

## 📱 Mobile vs Desktop Testing

### Response Time Expectations:
- **Mobile:** < 3 seconds (critical for usability)
- **Desktop:** < 2 seconds (optimal user experience)

### Mobile-Specific Checks:
- [ ] Slash commands appear in command picker
- [ ] Response embeds fit screen without horizontal scrolling
- [ ] Emojis render correctly
- [ ] Error messages are concise and clear

## 🧪 Test Cases

### 1. Basic Connectivity Test

**Commands to test:**
```
/status
```

**Expected Results:**
- Response time: < 2 seconds
- Shows 3 agents (Orchestrator, Backend, Database)
- All agents show "ready" status
- Clean, formatted embed display

**Mobile Check:**
- [ ] Embed fits mobile screen
- [ ] Status icons (✅) display correctly
- [ ] Text is readable without zooming

---

### 2. Task Assignment Test

**Commands to test:**
```
/assign-task description:"Create a simple Flask health check endpoint" task_type:"backend"
```

**Expected Results:**
- Response time: < 3 seconds
- Task assigned to BackendAgent
- Task ID generated (format: task_X_YYYYMMDD_HHMMSS)
- Next steps provided
- Orchestrator coordinates assignment

**Mobile Check:**
- [ ] Task description doesn't get cut off
- [ ] Task ID is copyable on mobile
- [ ] Next steps are clearly formatted

**Follow-up Test:**
```
/status
```
- Backend agent should show "busy" status
- Current task should be displayed

---

### 3. Agent Logs Test

**Commands to test:**
```
/agent-logs agent_name:"orchestrator"
/agent-logs agent_name:"backend"
/agent-logs agent_name:"database"
```

**Expected Results:**
- Response time: < 2 seconds each
- Shows current status, tasks completed, current task
- Last update timestamp
- No error messages

**Mobile Check:**
- [ ] Log entries are readable
- [ ] Timestamps format correctly
- [ ] Status information is clear

---

### 4. Task Approval Test

**Commands to test:**
```
/approve task_id:"[use_task_id_from_step_2]"
```

**Expected Results:**
- Response time: < 2 seconds
- Task marked as approved
- Backend agent returns to "ready" status
- Approved by and timestamp recorded

**Mobile Check:**
- [ ] Approval confirmation is prominent
- [ ] User mention displays correctly
- [ ] Timestamp is readable

---

### 5. Error Handling Tests

**Commands to test:**
```
/assign-task description:"" task_type:"invalid"
/approve task_id:"nonexistent_task"
/agent-logs agent_name:"invalid_agent"
```

**Expected Results:**
- Clear error messages for each case
- Helpful guidance on correct usage
- No system crashes or exceptions

**Mobile Check:**
- [ ] Error messages are concise
- [ ] Red error indicators (❌) visible
- [ ] Suggestions for correction provided

---

### 6. Admin Commands Test (Admin Users Only)

**Commands to test:**
```
/emergency-stop
```

**Expected Results:**
- Requires admin permissions
- Clear warning about consequences
- All agents set to "stopped" status
- All active tasks cleared

**Mobile Check:**
- [ ] Emergency warning is prominent
- [ ] Red indicators clearly visible
- [ ] Admin confirmation required

---

## 📊 Performance Benchmarks

### Response Time Targets:
- `/status`: < 1 second
- `/assign-task`: < 2 seconds  
- `/approve`: < 1 second
- `/agent-logs`: < 1.5 seconds
- `/emergency-stop`: < 1 second

### Mobile Usability Targets:
- All embeds fit in mobile viewport
- No horizontal scrolling required
- Emojis and formatting render correctly
- Touch targets are appropriately sized

## 🔧 Troubleshooting Common Issues

### Command Not Appearing:
1. Refresh Discord app (mobile: restart, desktop: Ctrl+Shift+R)
2. Check bot permissions in server settings
3. Verify bot has `applications.commands` scope
4. Wait 5-10 minutes for Discord sync

### Slow Response Times:
1. Check server internet connection
2. Monitor bot logs for errors
3. Verify agent initialization completed
4. Check system resource usage

### Mobile Display Issues:
1. Test on multiple mobile devices/screen sizes
2. Check embed field count (max 25, recommend <10 for mobile)
3. Verify message length < 2000 characters
4. Test with different Discord mobile app versions

## 📝 Test Result Documentation

For each test, record:

```
Test: [Test Name]
Platform: [Mobile/Desktop]
Response Time: [X.X seconds]
Status: [Pass/Fail]
Issues: [Any problems encountered]
Screenshots: [If UI issues]
```

## 🎯 Success Criteria

### Must Pass:
- [ ] All commands respond within time limits
- [ ] No error messages during normal operation
- [ ] Agent coordination works correctly
- [ ] Mobile display is fully functional
- [ ] Error handling is graceful and informative

### Should Pass:
- [ ] Response times consistently under 2 seconds
- [ ] Mobile UX score > 8/10
- [ ] All status updates accurate
- [ ] Task workflow completes end-to-end

## 🚀 Ready for Production Checklist

- [ ] All automated tests pass (run `python test_live_system.py`)
- [ ] All manual tests pass on both mobile and desktop
- [ ] Performance meets or exceeds benchmarks
- [ ] Error handling tested and working
- [ ] Admin commands properly restricted
- [ ] Mobile usability validated
- [ ] Agent coordination verified working
- [ ] Task assignment and approval workflow complete

## 📞 Next Steps After Testing

1. **If all tests pass:** System ready for production deployment
2. **If tests fail:** Address issues identified in recommendations
3. **Performance issues:** Optimize slow commands
4. **Mobile issues:** Adjust message formatting and embed design
5. **Agent issues:** Check dev bible loading and agent preparation

---

*Use this guide alongside the automated test suite for comprehensive validation.*