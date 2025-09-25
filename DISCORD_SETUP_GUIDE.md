# Discord Developer Portal Setup Guide

This guide walks you through setting up a Discord bot for the AI Agent Automation Hub.

## 🚀 Quick Setup Steps

### 1. Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Name your application (e.g., "AI Agent Hub Bot")
4. Click **"Create"**

### 2. Create a Bot

1. In your application, go to the **"Bot"** section in the left sidebar
2. Click **"Add Bot"**
3. Confirm by clicking **"Yes, do it!"**

### 3. Get Your Bot Token

1. In the Bot section, find **"Token"**
2. Click **"Copy"** to copy your bot token
3. **⚠️ IMPORTANT**: Keep this token secret! Never share it publicly
4. Add this token to your `.env` file:
   ```
   DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
   ```

### 4. Configure Bot Permissions

In the Bot section, enable these permissions:
- ✅ **Public Bot** (if you want others to invite it)
- ✅ **Requires OAuth2 Code Grant** (leave unchecked for simplicity)
- ✅ **Server Members Intent** (for member management)
- ✅ **Message Content Intent** (to read message content)

### 5. Set Bot Permissions (OAuth2)

1. Go to **"OAuth2"** → **"URL Generator"** in the left sidebar
2. Select **Scopes**:
   - ✅ `bot`
   - ✅ `applications.commands` (for slash commands)

3. Select **Bot Permissions**:
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Read Message History
   - ✅ View Channels
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Manage Messages (optional, for cleanup)
   - ✅ Add Reactions

4. Copy the generated URL from the bottom

### 6. Invite Bot to Your Server

1. Use the URL from step 5 to invite the bot to your Discord server
2. Make sure you have **Manage Server** permission on the target server
3. Select your server and click **"Authorize"**

### 7. Get Your Server (Guild) ID

1. In Discord, enable **Developer Mode**:
   - User Settings → Advanced → Developer Mode ✅
2. Right-click your server name in the server list
3. Click **"Copy Server ID"**
4. Add this to your `.env` file:
   ```
   DISCORD_GUILD_ID=YOUR_SERVER_ID_HERE
   ```

### 8. Get Channel IDs (Optional)

For specific channels (like status updates):
1. Right-click the channel name
2. Click **"Copy Channel ID"**
3. Add to your `.env` file:
   ```
   DISCORD_CHANNEL_ID=YOUR_CHANNEL_ID_HERE
   DISCORD_STATUS_CHANNEL_ID=YOUR_STATUS_CHANNEL_ID_HERE
   ```

## 📋 Complete .env Configuration

Your `.env` file should look like this:

```bash
# Discord Bot Configuration
DISCORD_TOKEN=OTxxxxxxxxxxxxxxxxxxxxx.Yxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxx
DISCORD_GUILD_ID=123456789012345678
DISCORD_CHANNEL_ID=123456789012345678
DISCORD_STATUS_CHANNEL_ID=123456789012345678

# Database Configuration  
DATABASE_URL=sqlite:///./data/local_test.db

# Application Configuration
APP_MODE=development
LOG_LEVEL=DEBUG

# GitHub Token (Optional)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 🧪 Testing Your Bot

After setup, test your bot:

1. Run the setup script:
   ```bash
   python setup_local_test.py
   ```

2. Run the validation:
   ```bash
   python scripts/validate_deployment.py
   ```

3. Start the bot (if all tests pass):
   ```bash
   python -m bot.main
   ```

## 🔧 Troubleshooting

### Bot Token Issues
- **Invalid token**: Make sure you copied the full token
- **Token reset**: If compromised, regenerate in the Bot section

### Permission Issues
- **Bot can't see channels**: Check channel permissions
- **Commands not working**: Ensure bot has slash command permissions
- **Can't send messages**: Verify "Send Messages" permission

### Server Issues
- **Bot not responding**: Check if bot is online in member list
- **Guild ID wrong**: Verify you copied the correct server ID
- **Channel not accessible**: Ensure bot has channel view permissions

## 🔒 Security Best Practices

1. **Never commit tokens**: Add `.env` to `.gitignore`
2. **Use environment variables**: Don't hardcode tokens in code
3. **Regenerate if compromised**: Reset token immediately if exposed
4. **Minimal permissions**: Only grant necessary bot permissions
5. **Monitor usage**: Check bot logs for unusual activity

## 📚 Additional Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [Discord Bot Permissions Calculator](https://discordapi.com/permissions.html)
- [Discord Server Template](https://discord.new/HsA6mBr8Kd) (Optional testing server)

## ⚡ Quick Commands Test

Once your bot is running, try these commands in Discord:

```
/ping                 # Test bot connectivity
/help                 # See available commands  
/assign-task          # Create a new task
/status               # Check system status
```

## 📞 Support

If you encounter issues:
1. Check the setup logs in `logs/local_setup.log`
2. Run the validation script for detailed diagnostics
3. Verify all environment variables are set correctly
4. Check Discord bot status in the Developer Portal