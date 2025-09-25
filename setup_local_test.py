#!/usr/bin/env python3
"""
Local Test Environment Setup Script
===================================

This script sets up a local testing environment for the AI Agent Automation Hub.
It validates environment variables, creates necessary directories, sets up SQLite
database, and tests module imports.

Usage: python setup_local_test.py
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class LocalTestSetup:
    """Local test environment setup manager."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.setup_results = {
            'timestamp': datetime.now().isoformat(),
            'environment_checks': {},
            'directory_setup': {},
            'database_setup': {},
            'import_tests': {},
            'overall_success': False
        }
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the setup process."""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "local_setup.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_environment_variables(self) -> bool:
        """Check and validate environment variables."""
        print("\n🔍 Checking Environment Variables...")
        print("=" * 50)
        
        # Load .env file if it exists
        env_file = self.project_root / '.env'
        if env_file.exists():
            self._load_env_file(env_file)
        
        required_vars = [
            'DISCORD_TOKEN',
            'DATABASE_URL', 
            'APP_MODE'
        ]
        
        optional_vars = [
            'DISCORD_GUILD_ID',
            'GITHUB_TOKEN',
            'LOG_LEVEL',
            'MAX_CONCURRENT_TASKS'
        ]
        
        missing_required = []
        missing_optional = []
        placeholder_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_required.append(var)
                print(f"❌ {var}: NOT SET")
            elif self._is_placeholder_value(value):
                placeholder_vars.append(var)
                print(f"⚠️  {var}: PLACEHOLDER VALUE - {value}")
            else:
                print(f"✅ {var}: SET")
        
        for var in optional_vars:
            value = os.getenv(var)
            if not value:
                missing_optional.append(var)
                print(f"⚪ {var}: NOT SET (optional)")
            elif self._is_placeholder_value(value):
                placeholder_vars.append(var)
                print(f"⚠️  {var}: PLACEHOLDER VALUE - {value}")
            else:
                print(f"✅ {var}: SET")
        
        # Store results
        self.setup_results['environment_checks'] = {
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'placeholder_vars': placeholder_vars,
            'env_file_exists': env_file.exists()
        }
        
        if missing_required:
            print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
            print("   Please update your .env file with actual values.")
            return False
        
        if placeholder_vars:
            print(f"\n⚠️  Placeholder values detected: {', '.join(placeholder_vars)}")
            print("   You'll need to replace these with actual values for full functionality.")
        
        print(f"\n✅ Environment validation {'completed with warnings' if placeholder_vars else 'passed'}")
        return True
    
    def _load_env_file(self, env_file: Path):
        """Load environment variables from .env file."""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Only set if not already set in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            self.logger.warning(f"Failed to load .env file: {e}")
    
    def _is_placeholder_value(self, value: str) -> bool:
        """Check if a value is a placeholder that needs replacement."""
        placeholders = [
            'YOUR_DISCORD_BOT_TOKEN_HERE',
            'YOUR_DISCORD_SERVER_ID_HERE', 
            'YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE',
            'your_discord_bot_token_here',
            'your_guild_id_here',
            'your_github_personal_access_token',
            'your_openai_api_key'
        ]
        return value in placeholders
    
    def setup_directories(self) -> bool:
        """Create necessary directories."""
        print("\n📁 Setting up directories...")
        print("=" * 50)
        
        directories = [
            'logs',
            'data',
            'data/sqlite', 
            'workspace',
            'temp',
            'backups'
        ]
        
        created_dirs = []
        failed_dirs = []
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dir_name)
                print(f"✅ {dir_name}/")
            except Exception as e:
                failed_dirs.append((dir_name, str(e)))
                print(f"❌ {dir_name}/ - Error: {e}")
        
        self.setup_results['directory_setup'] = {
            'created': created_dirs,
            'failed': failed_dirs
        }
        
        if failed_dirs:
            print(f"\n❌ Failed to create {len(failed_dirs)} directories")
            return False
        
        print(f"\n✅ Created {len(created_dirs)} directories successfully")
        return True
    
    def setup_sqlite_database(self) -> bool:
        """Setup local SQLite database for testing."""
        print("\n🗄️  Setting up SQLite database...")
        print("=" * 50)
        
        db_url = os.getenv('DATABASE_URL', 'sqlite:///./data/local_test.db')
        
        if not db_url.startswith('sqlite:///'):
            print("⚠️  DATABASE_URL is not SQLite, skipping database setup")
            return True
        
        # Extract database path from SQLite URL
        db_path = db_url.replace('sqlite:///', '')
        if not db_path.startswith('/'):
            db_path = self.project_root / db_path
        else:
            db_path = Path(db_path)
        
        try:
            # Ensure directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create database and basic tables
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Create basic tables for testing
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    component TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert sample data for testing
            cursor.execute('''
                INSERT OR IGNORE INTO agents (name, type) VALUES 
                ('backend-agent', 'backend'),
                ('testing-agent', 'testing'),
                ('orchestrator', 'orchestrator')
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO tasks (agent_id, title, description) VALUES 
                (1, 'Test backend functionality', 'Validate backend agent operations'),
                (2, 'Run test suite', 'Execute comprehensive testing'),
                (3, 'Coordinate agents', 'Manage agent interactions')
            ''')
            
            conn.commit()
            
            # Test database operations
            cursor.execute('SELECT COUNT(*) FROM agents')
            agent_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM tasks') 
            task_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✅ Database created: {db_path}")
            print(f"✅ Sample agents: {agent_count}")
            print(f"✅ Sample tasks: {task_count}")
            
            self.setup_results['database_setup'] = {
                'success': True,
                'database_path': str(db_path),
                'agent_count': agent_count,
                'task_count': task_count
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            self.setup_results['database_setup'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_module_imports(self) -> bool:
        """Test that all essential modules can be imported."""
        print("\n🐍 Testing module imports...")
        print("=" * 50)
        
        imports_to_test = [
            # Core Python modules
            ('os', 'Standard library'),
            ('sys', 'Standard library'),
            ('json', 'Standard library'), 
            ('sqlite3', 'Standard library'),
            ('pathlib.Path', 'Standard library'),
            ('datetime.datetime', 'Standard library'),
            
            # Third-party dependencies
            ('discord', 'Discord bot functionality'),
            ('asyncio', 'Async operations'),
            
            # Project modules (with fallbacks)
            ('database.models', 'Database models (optional)'),
            ('agents', 'Agent modules (optional)'),
        ]
        
        successful_imports = []
        failed_imports = []
        
        for import_spec, description in imports_to_test:
            try:
                if '.' in import_spec:
                    module_name, attr_name = import_spec.rsplit('.', 1)
                    module = __import__(module_name, fromlist=[attr_name])
                    getattr(module, attr_name)
                else:
                    __import__(import_spec)
                
                successful_imports.append(import_spec)
                print(f"✅ {import_spec} - {description}")
                
            except ImportError as e:
                failed_imports.append((import_spec, str(e)))
                if 'optional' in description.lower():
                    print(f"⚠️  {import_spec} - {description} (not found, but optional)")
                else:
                    print(f"❌ {import_spec} - {description} - Error: {e}")
            except Exception as e:
                failed_imports.append((import_spec, str(e)))
                print(f"❌ {import_spec} - {description} - Error: {e}")
        
        self.setup_results['import_tests'] = {
            'successful': successful_imports,
            'failed': failed_imports,
            'total_tested': len(imports_to_test)
        }
        
        critical_failures = [f for f in failed_imports if 'optional' not in f[0]]
        
        if critical_failures:
            print(f"\n❌ {len(critical_failures)} critical imports failed")
            print("   You may need to install dependencies with: pip install -r requirements.txt")
            return False
        
        print(f"\n✅ {len(successful_imports)} imports successful")
        if failed_imports:
            print(f"⚠️  {len(failed_imports)} optional imports failed (this is OK)")
        
        return True
    
    def generate_setup_report(self) -> str:
        """Generate a comprehensive setup report."""
        report = []
        report.append("🤖 AI Agent Automation Hub - Local Setup Report")
        report.append("=" * 60)
        report.append(f"📅 Setup Date: {self.setup_results['timestamp']}")
        report.append(f"📂 Project Root: {self.project_root}")
        report.append("")
        
        # Environment Check Results
        env_checks = self.setup_results['environment_checks']
        report.append("🔍 Environment Variables:")
        if env_checks.get('missing_required'):
            report.append(f"   ❌ Missing required: {', '.join(env_checks['missing_required'])}")
        else:
            report.append("   ✅ All required variables present")
        
        if env_checks.get('placeholder_vars'):
            report.append(f"   ⚠️  Placeholder values: {', '.join(env_checks['placeholder_vars'])}")
        
        # Directory Setup Results
        dir_setup = self.setup_results['directory_setup']
        report.append("")
        report.append("📁 Directory Setup:")
        report.append(f"   ✅ Created: {len(dir_setup.get('created', []))} directories")
        if dir_setup.get('failed'):
            report.append(f"   ❌ Failed: {len(dir_setup['failed'])} directories")
        
        # Database Setup Results
        db_setup = self.setup_results['database_setup']
        report.append("")
        report.append("🗄️  Database Setup:")
        if db_setup.get('success'):
            report.append(f"   ✅ SQLite database created")
            report.append(f"   📊 Sample agents: {db_setup.get('agent_count', 0)}")
            report.append(f"   📋 Sample tasks: {db_setup.get('task_count', 0)}")
        else:
            report.append(f"   ❌ Database setup failed: {db_setup.get('error', 'Unknown error')}")
        
        # Import Test Results
        import_tests = self.setup_results['import_tests']
        report.append("")
        report.append("🐍 Module Imports:")
        report.append(f"   ✅ Successful: {len(import_tests.get('successful', []))}")
        report.append(f"   ❌ Failed: {len(import_tests.get('failed', []))}")
        
        # Overall Status
        report.append("")
        report.append("📊 Overall Status:")
        if self.setup_results['overall_success']:
            report.append("   🎉 LOCAL SETUP COMPLETED SUCCESSFULLY!")
        else:
            report.append("   ⚠️  SETUP COMPLETED WITH ISSUES")
            report.append("      Please address the issues above before proceeding.")
        
        # Next Steps
        report.append("")
        report.append("🚀 Next Steps:")
        report.append("   1. Update placeholder values in .env file")
        report.append("   2. Run validation: python scripts/validate_deployment.py")
        report.append("   3. Start development: python -m agents.orchestrator.main")
        report.append("")
        
        return "\n".join(report)
    
    def run_setup(self) -> bool:
        """Run the complete setup process."""
        print("🚀 AI Agent Automation Hub - Local Test Setup")
        print("=" * 60)
        print(f"📂 Project Root: {self.project_root}")
        print(f"🕐 Setup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = True
        
        # Run setup steps
        success &= self.check_environment_variables()
        success &= self.setup_directories()
        success &= self.setup_sqlite_database()
        success &= self.test_module_imports()
        
        self.setup_results['overall_success'] = success
        
        # Generate and display report
        report = self.generate_setup_report()
        print("\n" + report)
        
        # Save report to file
        report_file = self.project_root / "logs" / "local_setup_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save detailed results as JSON
        results_file = self.project_root / "logs" / "local_setup_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.setup_results, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {report_file}")
        print(f"📊 Detailed results: {results_file}")
        
        return success


def main():
    """Main setup function."""
    try:
        setup = LocalTestSetup()
        success = setup.run_setup()
        
        if success:
            print("\n🎉 Setup completed successfully!")
            print("   You can now run: python scripts/validate_deployment.py")
            sys.exit(0)
        else:
            print("\n⚠️  Setup completed with issues.")
            print("   Please address the issues above before proceeding.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()