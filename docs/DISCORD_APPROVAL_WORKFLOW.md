# Discord Approval Workflow Documentation

## Overview

The Discord Approval Workflow enables complete mobile development cycle management through Discord slash commands. You can now approve, review, and reject pull requests directly from your phone, providing a seamless mobile development experience.

## New Discord Commands

### `/approve [pr-number]`
**Purpose**: Approve and merge a specific pull request
**Usage**: `/approve 42`
**Features**:
- Validates PR is mergeable before attempting merge
- Automatically merges to main branch
- Updates associated task status in database
- Sends confirmation with merge commit SHA
- Logs approval activity for audit trail

**Example Response**:
```
✅ PR Approved and Merged
PR #42 has been successfully merged by @username

PR Title: Add user authentication feature
Merge Commit: a1b2c3d4
Approved by: username
```

### `/review [pr-number]`
**Purpose**: Show detailed PR information with interactive approve/reject buttons
**Usage**: `/review 42`
**Features**:
- Displays comprehensive PR details (title, description, files changed, etc.)
- Shows mergeable status and conflict information
- Provides interactive ✅ Approve and ❌ Reject buttons
- Includes 🔄 Refresh button for real-time updates
- Mobile-optimized for quick decision making

**Example Response**:
```
🔍 PR #42 - Review
Add user authentication feature

📊 Changes          🔄 Status           👤 Author
Files: 8            State: Open         johndoe
+156 -23            Mergeable: ✅       feature/auth → main

📝 Description
Implements JWT-based authentication with:
- Login/logout endpoints
- Password hashing with bcrypt
- Session management
- Input validation

📁 Files Changed
• `src/auth/login.py`
• `src/auth/middleware.py`
• `tests/test_auth.py`
... and 5 more files

⏰ Timeline
Created: 2024-09-23
Updated: 2024-09-23

[✅ Approve & Merge] [❌ Reject] [🔄 Refresh]
```

### `/reject [pr-number] [reason]`
**Purpose**: Reject a pull request with a specific reason
**Usage**: `/reject 42 "Needs more comprehensive tests before merging"`
**Features**:
- Closes PR with provided reason
- Adds rejection comment to PR
- Updates task status to reflect rejection
- Logs rejection activity with reason

**Example Response**:
```
❌ PR Rejected
PR #42 has been rejected by @username

PR Title: Add user authentication feature
Reason: Needs more comprehensive tests before merging
Rejected by: username
```

### `/pending-prs [limit]`
**Purpose**: Show all open pull requests awaiting approval
**Usage**: `/pending-prs 10`
**Features**:
- Lists open PRs with status indicators
- Shows draft status and merge conflicts
- Links associated task IDs when available
- Provides quick access to review each PR

**Example Response**:
```
📋 Pending Pull Requests (3)

#42 - Add user authentication feature
Task: sep23-001 • by johndoe
[View PR](https://github.com/repo/pull/42)

#43 - Fix database connection pooling
🚧 Draft • by janedoe
[View PR](https://github.com/repo/pull/43)

#44 - Update API documentation
⚠️ Conflicts • Task: sep23-002 • by bobsmith
[View PR](https://github.com/repo/pull/44)

Use /review [pr-number] to see details and approve/reject
```

### `/status` (Enhanced)
**Purpose**: Get comprehensive system status including PR metrics
**Usage**: `/status`
**Features**:
- Shows pending PRs awaiting approval
- Displays agent performance metrics
- GitHub integration status
- Real-time activity alerts
- Quick action shortcuts

**Example Response**:
```
🤖 Automation Hub Status

🔧 System           📋 Active Tasks      🔄 Pull Requests
Status: Active      Total: 12           Open PRs: 5
Uptime: 2d 4h       Pending: 3          Awaiting Approval: 2
GitHub: ✅          In Progress: 2      Recent Activity: 1 merged
                    Completed: 7

📊 Agent Performance
Success Rate: 94.2%
Tasks/Day: 6
Avg Response: 2.34s
Errors: 1

🔔 Alerts
⏳ 2 PRs need approval
📝 3 tasks pending

🐙 GitHub Integration
Repository: VictorGavo/ai-agent-automation-hub
Operations: 15 commits, 8 PRs
Success Rate: 98.7%

💡 /pending-prs • /assign-task • /review [pr-number] • /approve [pr-number]
```

## Mobile Workflow

### Complete Development Cycle on Mobile

1. **Task Creation**
   ```
   /assign-task "Add rate limiting to API endpoints" priority:high
   ```

2. **Monitor Progress**
   ```
   /status
   ```

3. **PR Review Notification**
   - Receive notification when PR is ready
   - Use `/pending-prs` to see all waiting PRs

4. **Interactive Review**
   ```
   /review 42
   ```
   - See full PR details
   - Tap ✅ Approve or ❌ Reject buttons

5. **Quick Actions**
   - **Approve**: Tap ✅ → Instant merge
   - **Reject**: Tap ❌ → Enter reason → Close PR

6. **Confirmation**
   - Get immediate feedback
   - Task status automatically updated
   - Audit trail maintained

### Mobile-Optimized Features

- **Interactive Buttons**: No need to type commands for approve/reject
- **Detailed Summaries**: All essential PR info in one view
- **Real-time Updates**: Refresh button for latest status
- **Quick Navigation**: Direct links to GitHub PRs
- **Status Indicators**: Visual icons for merge conflicts, drafts, etc.
- **Compact Layout**: Optimized for mobile screens

## Integration with Existing System

### Task Management Integration
- PR approvals automatically update task status
- Task IDs are linked to PRs in listings
- Human approval requirements are respected
- Completion triggers task finalization

### GitHub Integration
- Uses existing GitHubClient for all operations
- Maintains security through GitHub permissions
- Preserves PR comments and history
- Supports all GitHub merge strategies

### Database Updates
- Approval/rejection logged with user attribution
- Task status transitions tracked
- Performance metrics updated
- Audit trail maintained for compliance

## Security and Permissions

### Discord Permissions
- Commands respect Discord server permissions
- User attributions logged for audit trail
- Rate limiting prevents abuse

### GitHub Permissions
- Uses configured GitHub token permissions
- Respects repository access controls
- Maintains GitHub's review processes
- Preserves branch protection rules

## Error Handling

### Common Scenarios
- **PR Not Found**: Clear error message with suggestions
- **Merge Conflicts**: Status shown with resolution guidance
- **GitHub API Errors**: Graceful fallback with retry options
- **Permission Issues**: Clear explanation of required permissions

### Mobile-Friendly Error Messages
```
❌ Approval Failed
PR #42 cannot be merged due to conflicts.

Next Steps:
• Ask the author to resolve conflicts
• Use /review 42 to see current status
• Check GitHub for detailed conflict info
```

## Performance Considerations

### Response Times
- Commands respond within 2-5 seconds
- Interactive buttons provide immediate feedback
- Background processing for complex operations
- Graceful degradation under load

### Rate Limiting
- Built-in Discord rate limit compliance
- GitHub API rate limit monitoring
- Queued operations for burst scenarios
- User feedback for temporary delays

## Troubleshooting

### Setup Issues
1. **Missing Commands**: Ensure bot has been restarted and commands synced
2. **Permission Errors**: Verify Discord and GitHub permissions
3. **GitHub Connection**: Check GITHUB_TOKEN environment variable
4. **Database Issues**: Verify DATABASE_URL configuration

### Common Problems
- **Commands Not Appearing**: Bot needs `applications.commands` scope
- **Buttons Not Working**: Bot needs message permissions
- **PR Not Found**: Verify PR number and repository access
- **Merge Failures**: Check for conflicts or branch protection

## Future Enhancements

### Planned Features
- Bulk PR operations
- Custom approval workflows
- Integration with code review tools
- Advanced PR analytics
- Automated conflict resolution suggestions

### Mobile App Integration
- Push notifications for PR events
- Offline review capabilities
- Voice command support
- Custom notification preferences

## API Reference

### Command Parameters
```typescript
/approve {
  pr_number: number  // Required: PR number to approve
}

/review {
  pr_number: number  // Required: PR number to review
}

/reject {
  pr_number: number,  // Required: PR number to reject
  reason: string      // Required: Rejection reason
}

/pending-prs {
  limit?: number      // Optional: Max PRs to show (default: 10, max: 20)
}
```

### Response Types
```typescript
interface ApprovalResponse {
  success: boolean;
  message: string;
  pr_title?: string;
  sha?: string;
}

interface PRDetails {
  number: number;
  title: string;
  body: string;
  state: string;
  mergeable: boolean;
  author: string;
  files_changed: string[];
  additions: number;
  deletions: number;
  url: string;
}
```

This completes the Discord Approval Workflow implementation, providing a comprehensive mobile-friendly development cycle management system.