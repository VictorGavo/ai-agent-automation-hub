"""
Discord Bot Configuration

This module handles configuration management for the Discord bot,
including environment variables, settings validation, and default values.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BotConfig:
    """Configuration class for Discord bot settings."""
    
    # Discord Configuration
    discord_token: str
    command_prefix: str = "!"
    status_channel_id: Optional[str] = None
    
    # Agent Configuration
    max_concurrent_tasks: int = 10
    task_timeout_minutes: int = 60
    status_update_interval_minutes: int = 30
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/discord_bot.log"
    
    # Security Configuration
    admin_role_name: str = "Admin"
    allowed_guilds: Optional[list] = None
    
    # Database Configuration (optional)
    database_url: Optional[str] = None
    
    # GitHub Configuration (optional)
    github_token: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Create configuration from environment variables."""
        
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if not discord_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
        
        # Parse allowed guilds if provided
        allowed_guilds = None
        guilds_env = os.getenv('DISCORD_ALLOWED_GUILDS')
        if guilds_env:
            allowed_guilds = [int(g.strip()) for g in guilds_env.split(',') if g.strip()]
        
        return cls(
            discord_token=discord_token,
            command_prefix=os.getenv('DISCORD_COMMAND_PREFIX', '!'),
            status_channel_id=os.getenv('DISCORD_STATUS_CHANNEL_ID'),
            max_concurrent_tasks=int(os.getenv('BOT_MAX_CONCURRENT_TASKS', '10')),
            task_timeout_minutes=int(os.getenv('BOT_TASK_TIMEOUT_MINUTES', '60')),
            status_update_interval_minutes=int(os.getenv('BOT_STATUS_UPDATE_INTERVAL', '30')),
            log_level=os.getenv('BOT_LOG_LEVEL', 'INFO'),
            log_file=os.getenv('BOT_LOG_FILE', 'logs/discord_bot.log'),
            admin_role_name=os.getenv('DISCORD_ADMIN_ROLE', 'Admin'),
            allowed_guilds=allowed_guilds,
            database_url=os.getenv('DATABASE_URL'),
            github_token=os.getenv('GITHUB_TOKEN')
        )
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return validation results."""
        issues = []
        warnings = []
        
        # Required validations
        if not self.discord_token:
            issues.append("Discord token is required")
        
        if self.max_concurrent_tasks <= 0:
            issues.append("Max concurrent tasks must be positive")
        
        if self.task_timeout_minutes <= 0:
            issues.append("Task timeout must be positive")
        
        if self.status_update_interval_minutes <= 0:
            issues.append("Status update interval must be positive")
        
        # Optional validations (warnings)
        if not self.github_token:
            warnings.append("GitHub token not provided - GitHub integration disabled")
        
        if not self.database_url:
            warnings.append("Database URL not provided - database features disabled")
        
        if not self.status_channel_id:
            warnings.append("Status channel not configured - periodic updates disabled")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        config_dict = {
            'command_prefix': self.command_prefix,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'task_timeout_minutes': self.task_timeout_minutes,
            'status_update_interval_minutes': self.status_update_interval_minutes,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'admin_role_name': self.admin_role_name,
            'has_github_token': bool(self.github_token),
            'has_database_url': bool(self.database_url),
            'has_status_channel': bool(self.status_channel_id),
            'allowed_guilds_count': len(self.allowed_guilds) if self.allowed_guilds else 0
        }
        
        return config_dict


# Global configuration instance
config: Optional[BotConfig] = None


def get_config() -> BotConfig:
    """Get the global configuration instance."""
    global config
    
    if config is None:
        config = BotConfig.from_env()
        validation = config.validate()
        
        if not validation['valid']:
            raise ValueError(f"Configuration validation failed: {validation['issues']}")
    
    return config


def reload_config() -> BotConfig:
    """Reload configuration from environment variables."""
    global config
    config = None
    return get_config()


# Environment variable template for documentation
ENVIRONMENT_TEMPLATE = """
# Required Environment Variables
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Optional Discord Configuration
DISCORD_COMMAND_PREFIX=!
DISCORD_STATUS_CHANNEL_ID=channel_id_for_status_updates
DISCORD_ALLOWED_GUILDS=guild_id_1,guild_id_2
DISCORD_ADMIN_ROLE=Admin

# Optional Bot Configuration
BOT_MAX_CONCURRENT_TASKS=10
BOT_TASK_TIMEOUT_MINUTES=60
BOT_STATUS_UPDATE_INTERVAL=30
BOT_LOG_LEVEL=INFO
BOT_LOG_FILE=logs/discord_bot.log

# Optional Integration Configuration
GITHUB_TOKEN=your_github_token_here
DATABASE_URL=postgresql://user:password@localhost/dbname
"""


def generate_env_template(file_path: str = '.env.bot.template') -> None:
    """Generate an environment template file."""
    with open(file_path, 'w') as f:
        f.write(ENVIRONMENT_TEMPLATE.strip())
    
    print(f"Environment template generated at: {file_path}")


if __name__ == "__main__":
    # Generate environment template if run directly
    generate_env_template()
    
    # Test configuration loading
    try:
        config = get_config()
        validation = config.validate()
        
        print("Configuration loaded successfully!")
        print(f"Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        
        if validation['issues']:
            print("Issues:")
            for issue in validation['issues']:
                print(f"  - {issue}")
        
        if validation['warnings']:
            print("Warnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        print("\nConfiguration:")
        for key, value in config.to_dict().items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Configuration error: {e}")