"""
Safety Monitor Service

Monitors AI agent operations and system health to provide automated safety features:
- Watches for agent errors and creates recovery points
- Prevents file conflicts between multiple agents
- Monitors system resources on Raspberry Pi
- Sends Discord alerts for manual intervention
"""

import os
import sys
import asyncio
import logging
import threading
import time
import psutil
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import sqlite3
from contextlib import contextmanager
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.task_state_manager import get_task_state_manager, TaskState, CheckpointType
from utils.safe_git_operations import get_safe_git_operations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringEvent(Enum):
    """Types of monitoring events."""
    AGENT_ERROR = "agent_error"
    RESOURCE_WARNING = "resource_warning"
    FILE_CONFLICT = "file_conflict"
    SYSTEM_OVERLOAD = "system_overload"
    RECOVERY_POINT = "recovery_point"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class SafetyAlert:
    """Represents a safety alert."""
    alert_id: str
    event_type: MonitoringEvent
    level: AlertLevel
    timestamp: datetime
    agent_name: Optional[str]
    title: str
    description: str
    data: Dict[str, Any]
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolution_timestamp:
            data['resolution_timestamp'] = self.resolution_timestamp.isoformat()
        return data


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: List[float]
    agent_count: int
    active_tasks: int
    temperature: Optional[float] = None
    
    def is_overloaded(self) -> bool:
        """Check if system is overloaded."""
        return (
            self.cpu_percent > 80 or
            self.memory_percent > 85 or
            self.load_average[0] > 4.0 or  # 1-minute load average
            (self.temperature and self.temperature > 75)
        )
    
    def get_warnings(self) -> List[str]:
        """Get system warning messages."""
        warnings = []
        
        if self.cpu_percent > 70:
            warnings.append(f"High CPU usage: {self.cpu_percent:.1f}%")
        
        if self.memory_percent > 75:
            warnings.append(f"High memory usage: {self.memory_percent:.1f}%")
        
        if self.disk_percent > 85:
            warnings.append(f"High disk usage: {self.disk_percent:.1f}%")
        
        if self.load_average[0] > 2.0:
            warnings.append(f"High load average: {self.load_average[0]:.2f}")
        
        if self.temperature and self.temperature > 65:
            warnings.append(f"High temperature: {self.temperature:.1f}°C")
        
        return warnings


class FileAccessTracker:
    """Tracks file access by agents to prevent conflicts."""
    
    def __init__(self):
        self._file_locks: Dict[str, str] = {}  # file_path -> agent_name
        self._access_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def request_file_access(self, agent_name: str, file_path: str, operation: str = "modify") -> bool:
        """
        Request exclusive access to a file.
        
        Args:
            agent_name: Name of requesting agent
            file_path: Path to file
            operation: Type of operation (read, modify, create)
            
        Returns:
            True if access granted
        """
        with self._lock:
            abs_path = os.path.abspath(file_path)
            
            # Check if file is already locked by another agent
            if abs_path in self._file_locks and self._file_locks[abs_path] != agent_name:
                logger.warning(f"File access denied - already locked by {self._file_locks[abs_path]}: {abs_path}")
                return False
            
            # Grant access
            self._file_locks[abs_path] = agent_name
            
            # Record access
            self._access_history.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'agent_name': agent_name,
                'file_path': abs_path,
                'operation': operation,
                'granted': True
            })
            
            # Keep only last 100 entries
            self._access_history = self._access_history[-100:]
            
            logger.debug(f"File access granted to {agent_name}: {abs_path}")
            return True
    
    def release_file_access(self, agent_name: str, file_path: str) -> None:
        """Release file access."""
        with self._lock:
            abs_path = os.path.abspath(file_path)
            
            if abs_path in self._file_locks and self._file_locks[abs_path] == agent_name:
                del self._file_locks[abs_path]
                logger.debug(f"File access released by {agent_name}: {abs_path}")
    
    def get_locked_files(self, agent_name: Optional[str] = None) -> Dict[str, str]:
        """Get currently locked files."""
        with self._lock:
            if agent_name:
                return {path: agent for path, agent in self._file_locks.items() if agent == agent_name}
            return self._file_locks.copy()
    
    def get_access_history(self) -> List[Dict[str, Any]]:
        """Get recent file access history."""
        with self._lock:
            return self._access_history.copy()


class SafetyMonitor:
    """
    Central safety monitoring service for AI agents.
    
    Features:
    - Error monitoring and recovery point creation
    - File access conflict prevention
    - System resource monitoring
    - Discord alert integration
    - Automatic agent pausing on overload
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize safety monitor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.db_path = self.config.get('db_path', 'data/safety_monitor.db')
        self.monitoring_interval = self.config.get('monitoring_interval', 30)  # seconds
        self.alert_cooldown = self.config.get('alert_cooldown', 300)  # 5 minutes
        
        # Initialize components
        self.task_state_manager = get_task_state_manager()
        self.safe_git = get_safe_git_operations()
        self.file_tracker = FileAccessTracker()
        
        # State tracking
        self.is_running = False
        self.safe_mode_active = False
        self.paused_agents: Set[str] = set()
        self.last_alerts: Dict[str, datetime] = {}
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Discord integration (placeholder)
        self.discord_webhook_url = self.config.get('discord_webhook_url')
        
        # Initialize database
        self._init_database()
        
        logger.info("SafetyMonitor initialized")
    
    def _init_database(self) -> None:
        """Initialize monitoring database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_connection() as conn:
            # Alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS safety_alerts (
                    alert_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    data TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_timestamp TEXT,
                    resolution_notes TEXT
                )
            """)
            
            # System metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_percent REAL NOT NULL,
                    load_average TEXT NOT NULL,
                    agent_count INTEGER NOT NULL,
                    active_tasks INTEGER NOT NULL,
                    temperature REAL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON safety_alerts (timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_level ON safety_alerts (level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics (timestamp)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            yield conn
        finally:
            conn.close()
    
    def start_monitoring(self) -> None:
        """Start the safety monitoring service."""
        if self.is_running:
            logger.warning("Safety monitor already running")
            return
        
        with self._lock:
            self.is_running = True
            self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self._monitor_thread.start()
        
        logger.info("Safety monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop the safety monitoring service."""
        with self._lock:
            self.is_running = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        logger.info("Safety monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                self._store_system_metrics(metrics)
                
                # Check for system overload
                if metrics.is_overloaded():
                    self._handle_system_overload(metrics)
                
                # Check agent errors
                self._check_agent_errors()
                
                # Check for stale tasks
                self._check_stale_tasks()
                
                # Generate warnings
                warnings = metrics.get_warnings()
                if warnings:
                    self._create_alert(
                        MonitoringEvent.RESOURCE_WARNING,
                        AlertLevel.WARNING,
                        "System Resource Warning",
                        f"System warnings detected: {', '.join(warnings)}",
                        {'warnings': warnings, 'metrics': asdict(metrics)}
                    )
                
                time.sleep(self.monitoring_interval)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(min(self.monitoring_interval, 60))  # Fallback interval
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        load_avg = os.getloadavg()
        
        # Count active agents and tasks
        agent_tasks = self.task_state_manager.get_agent_tasks("*")  # Placeholder - need to implement wildcard
        active_tasks = len([t for t in agent_tasks if t.state == TaskState.IN_PROGRESS])
        
        # Try to get Pi temperature
        temperature = None
        try:
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temperature = float(f.read().strip()) / 1000.0
        except Exception:
            pass
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            load_average=list(load_avg),
            agent_count=len(set(t.agent_name for t in agent_tasks)),
            active_tasks=active_tasks,
            temperature=temperature
        )
    
    def _store_system_metrics(self, metrics: SystemMetrics) -> None:
        """Store system metrics in database."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, disk_percent,
                        load_average, agent_count, active_tasks, temperature
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(timezone.utc).isoformat(),
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_percent,
                    json.dumps(metrics.load_average),
                    metrics.agent_count,
                    metrics.active_tasks,
                    metrics.temperature
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store system metrics: {e}")
    
    def _handle_system_overload(self, metrics: SystemMetrics) -> None:
        """Handle system overload condition."""
        if not self._should_send_alert("system_overload"):
            return
        
        # Create critical alert
        self._create_alert(
            MonitoringEvent.SYSTEM_OVERLOAD,
            AlertLevel.CRITICAL,
            "System Overload Detected",
            f"System is overloaded - CPU: {metrics.cpu_percent:.1f}%, "
            f"Memory: {metrics.memory_percent:.1f}%, Load: {metrics.load_average[0]:.2f}",
            {'metrics': asdict(metrics), 'auto_pause_triggered': True}
        )
        
        # Automatically pause agents in safe mode
        if not self.safe_mode_active:
            logger.critical("System overload detected - activating safe mode")
            self.activate_safe_mode("System overload detected")
    
    def _check_agent_errors(self) -> None:
        """Check for agent errors and create recovery points."""
        # This would integrate with agent error reporting
        # For now, it's a placeholder for the monitoring framework
        pass
    
    def _check_stale_tasks(self) -> None:
        """Check for stale or stuck tasks."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=2)
            
            # This is a placeholder - would need to implement proper task querying
            # Check for tasks that have been in progress for too long
            pass
        
        except Exception as e:
            logger.error(f"Error checking stale tasks: {e}")
    
    def _create_alert(
        self,
        event_type: MonitoringEvent,
        level: AlertLevel,
        title: str,
        description: str,
        data: Dict[str, Any],
        agent_name: Optional[str] = None
    ) -> str:
        """Create and store safety alert."""
        alert_id = f"{event_type.value}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        alert = SafetyAlert(
            alert_id=alert_id,
            event_type=event_type,
            level=level,
            timestamp=datetime.now(timezone.utc),
            agent_name=agent_name,
            title=title,
            description=description,
            data=data
        )
        
        # Store in database
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO safety_alerts (
                        alert_id, event_type, level, timestamp, agent_name,
                        title, description, data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_id,
                    alert.event_type.value,
                    alert.level.value,
                    alert.timestamp.isoformat(),
                    alert.agent_name,
                    alert.title,
                    alert.description,
                    json.dumps(alert.data)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
        
        # Send Discord notification
        self._send_discord_alert(alert)
        
        # Update last alert time
        self.last_alerts[f"{event_type.value}_{agent_name or 'system'}"] = alert.timestamp
        
        logger.info(f"Created {level.value} alert: {title}")
        return alert_id
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent (cooldown check)."""
        last_alert = self.last_alerts.get(alert_key)
        if not last_alert:
            return True
        
        time_since_last = datetime.now(timezone.utc) - last_alert
        return time_since_last.total_seconds() >= self.alert_cooldown
    
    def _send_discord_alert(self, alert: SafetyAlert) -> None:
        """Send alert to Discord (placeholder)."""
        if not self.discord_webhook_url:
            return
        
        # This would implement actual Discord webhook integration
        logger.info(f"Would send Discord alert: {alert.title}")
    
    def activate_safe_mode(self, reason: str) -> None:
        """Activate safe mode - pause all agents."""
        with self._lock:
            if self.safe_mode_active:
                logger.warning("Safe mode already active")
                return
            
            self.safe_mode_active = True
            
            # Create alert
            self._create_alert(
                MonitoringEvent.MANUAL_INTERVENTION,
                AlertLevel.CRITICAL,
                "Safe Mode Activated",
                f"Safe mode activated: {reason}",
                {'reason': reason, 'timestamp': datetime.now(timezone.utc).isoformat()}
            )
            
            logger.critical(f"Safe mode activated: {reason}")
    
    def deactivate_safe_mode(self) -> None:
        """Deactivate safe mode."""
        with self._lock:
            if not self.safe_mode_active:
                logger.warning("Safe mode not active")
                return
            
            self.safe_mode_active = False
            self.paused_agents.clear()
            
            logger.info("Safe mode deactivated")
    
    def pause_agent(self, agent_name: str, reason: str) -> None:
        """Pause specific agent."""
        with self._lock:
            self.paused_agents.add(agent_name)
            
            self._create_alert(
                MonitoringEvent.MANUAL_INTERVENTION,
                AlertLevel.WARNING,
                f"Agent Paused: {agent_name}",
                f"Agent paused: {reason}",
                {'agent_name': agent_name, 'reason': reason},
                agent_name=agent_name
            )
            
            logger.warning(f"Paused agent {agent_name}: {reason}")
    
    def resume_agent(self, agent_name: str) -> None:
        """Resume paused agent."""
        with self._lock:
            self.paused_agents.discard(agent_name)
            logger.info(f"Resumed agent: {agent_name}")
    
    def is_agent_paused(self, agent_name: str) -> bool:
        """Check if agent is paused."""
        return self.safe_mode_active or agent_name in self.paused_agents
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        metrics = self._collect_system_metrics()
        
        # Get recent alerts
        recent_alerts = []
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM safety_alerts 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """, (
                    (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
                ))
                
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    alert_data = dict(zip(columns, row))
                    alert_data['data'] = json.loads(alert_data['data'])
                    recent_alerts.append(alert_data)
        
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system_metrics': asdict(metrics),
            'is_overloaded': metrics.is_overloaded(),
            'warnings': metrics.get_warnings(),
            'safe_mode_active': self.safe_mode_active,
            'paused_agents': list(self.paused_agents),
            'monitoring_active': self.is_running,
            'recent_alerts': recent_alerts,
            'file_locks': self.file_tracker.get_locked_files(),
            'git_status': self.safe_git.get_safety_status()
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Clean up old monitoring data."""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).isoformat()
        
        stats = {
            'alerts_deleted': 0,
            'metrics_deleted': 0
        }
        
        try:
            with self._get_connection() as conn:
                # Count and delete old alerts
                cursor = conn.execute("SELECT COUNT(*) FROM safety_alerts WHERE timestamp < ?", (cutoff_date,))
                stats['alerts_deleted'] = cursor.fetchone()[0]
                
                conn.execute("DELETE FROM safety_alerts WHERE timestamp < ?", (cutoff_date,))
                
                # Count and delete old metrics
                cursor = conn.execute("SELECT COUNT(*) FROM system_metrics WHERE timestamp < ?", (cutoff_date,))
                stats['metrics_deleted'] = cursor.fetchone()[0]
                
                conn.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff_date,))
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info(f"Cleanup completed: {stats}")
        return stats


# Global instance
_safety_monitor: Optional[SafetyMonitor] = None


def get_safety_monitor(config: Optional[Dict[str, Any]] = None) -> SafetyMonitor:
    """Get global safety monitor instance."""
    global _safety_monitor
    
    if _safety_monitor is None:
        _safety_monitor = SafetyMonitor(config)
    
    return _safety_monitor


if __name__ == "__main__":
    # Test the safety monitor
    try:
        print("Testing SafetyMonitor...")
        
        monitor = SafetyMonitor({
            'db_path': 'test_safety_monitor.db',
            'monitoring_interval': 5
        })
        
        # Test system metrics collection
        metrics = monitor._collect_system_metrics()
        print(f"✓ System metrics: CPU={metrics.cpu_percent:.1f}%, Memory={metrics.memory_percent:.1f}%")
        
        # Test alert creation
        alert_id = monitor._create_alert(
            MonitoringEvent.AGENT_ERROR,
            AlertLevel.WARNING,
            "Test Alert",
            "This is a test alert",
            {'test_data': True}
        )
        print(f"✓ Created alert: {alert_id}")
        
        # Test safe mode
        monitor.activate_safe_mode("Test activation")
        print(f"✓ Safe mode active: {monitor.safe_mode_active}")
        
        monitor.deactivate_safe_mode()
        print(f"✓ Safe mode deactivated: {not monitor.safe_mode_active}")
        
        # Test health status
        health = monitor.get_system_health()
        print(f"✓ System health: {len(health['recent_alerts'])} alerts, overloaded={health['is_overloaded']}")
        
        print("\n✅ All SafetyMonitor tests passed!")
        
        # Cleanup test database
        os.remove('test_safety_monitor.db')
        
    except Exception as e:
        print(f"❌ SafetyMonitor test failed: {e}")
        raise