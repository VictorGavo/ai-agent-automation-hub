# scripts/init_database.py
"""Database initialization script for AI Agent Automation Hub"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from database.models.base import Base, DATABASE_URL
from database.models.task import Task, TaskCategory, TaskPriority, TaskStatus
from database.models.agent import Agent, AgentType, AgentStatus
from database.models.logs import Log, LogLevel
from datetime import datetime, timezone
import uuid

def create_database():
    """Create database and tables"""
    print("🔧 Initializing database...")
    
    try:
        engine = create_engine(DATABASE_URL, echo=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Insert initial data
        insert_initial_data(engine)
        print("✅ Initial data inserted successfully")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)

def insert_initial_data(engine):
    """Insert initial system data"""
    from sqlalchemy.orm import sessionmaker
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create Orchestrator Agent
        orchestrator = Agent(
            name="orchestrator-alpha",
            type=AgentType.ORCHESTRATOR,
            status=AgentStatus.ACTIVE,
            capabilities=[
                "task_assignment",
                "agent_coordination", 
                "human_interaction",
                "task_validation",
                "progress_monitoring"
            ],
            performance_metrics={
                "tasks_assigned": 0,
                "successful_completions": 0,
                "average_response_time": 0.0
            },
            configuration={
                "max_clarifying_questions": 5,
                "task_timeout_hours": 4,
                "escalation_threshold_minutes": 15
            }
        )
        
        db.add(orchestrator)
        
        # Create initial system log
        system_log = Log(
            agent_name="system",
            level=LogLevel.INFO,
            message="Automation Hub database initialized successfully",
            context="database_init",
            metadata='{"initialization": true, "version": "1.0.0"}'
        )
        
        db.add(system_log)
        
        # Create sample task for testing
        sample_task = Task(
            title="System Health Check",
            description="Verify all components are working correctly",
            category=TaskCategory.GENERAL,
            priority=TaskPriority.LOW,
            status=TaskStatus.COMPLETED,
            assigned_agent="orchestrator-alpha",
            estimated_hours=0.1,
            actual_hours=0.1,
            human_approval_required=False,
            discord_user_id="system",
            discord_channel_id="system",
            success_criteria=[
                "Database connection verified",
                "Agent registration confirmed",
                "Logging system functional"
            ],
            completed_at=datetime.now(timezone.utc)
        )
        
        db.add(sample_task)
        
        db.commit()
        print("✅ Initial agents and sample data created")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting initial data: {e}")
        raise
    finally:
        db.close()

def verify_database():
    """Verify database setup"""
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test basic queries
        agent_count = db.query(Agent).count()
        task_count = db.query(Task).count()
        log_count = db.query(Log).count()
        
        print(f"✅ Database verification successful:")
        print(f"   - Agents: {agent_count}")
        print(f"   - Tasks: {task_count}")
        print(f"   - Logs: {log_count}")
        
        # Test specific queries
        orchestrator = db.query(Agent).filter(Agent.name == "orchestrator-alpha").first()
        if orchestrator:
            print(f"   - Orchestrator Agent: {orchestrator.status.value}")
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 AI Agent Automation Hub - Database Setup")
    print("=" * 50)
    
    create_database()
    verify_database()
    
    print("\n✅ Database initialization complete!")
    print("🎯 Next steps:")
    print("   1. Start PostgreSQL: docker-compose up -d postgres")
    print("   2. Run this script: python scripts/init_database.py")
    print("   3. Start Orchestrator: docker-compose up -d orchestrator")
    print("   4. Test Discord bot: /ping command in Discord")