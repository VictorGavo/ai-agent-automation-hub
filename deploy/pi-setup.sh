#!/bin/bash

# AI Agent Automation Hub - Raspberry Pi 5 Setup Script
# This script sets up Docker and deploys the AI agent system on Raspberry Pi 5

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="/opt/automation-hub/data"
LOG_FILE="/var/log/automation-hub-setup.log"
SERVICE_USER="aiagent"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_pi5() {
    local model=$(cat /proc/device-tree/model 2>/dev/null || echo "Unknown")
    if [[ ! "$model" =~ "Raspberry Pi 5" ]]; then
        log_warning "This script is optimized for Raspberry Pi 5, detected: $model"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "Raspberry Pi 5 detected"
    fi
}

update_system() {
    log "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
    apt-get install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        unzip \
        ca-certificates \
        gnupg \
        lsb-release \
        apt-transport-https \
        software-properties-common
    log_success "System updated"
}

install_docker() {
    log "Installing Docker..."
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        log_warning "Docker is already installed"
        docker --version
    else
        # Install Docker using convenience script for ARM64
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        
        # Start and enable Docker service
        systemctl start docker
        systemctl enable docker
        
        # Add current user to docker group (if not root)
        if [ "$SUDO_USER" ]; then
            usermod -aG docker "$SUDO_USER"
            log_success "Added $SUDO_USER to docker group"
        fi
        
        log_success "Docker installed successfully"
    fi
    
    # Install Docker Compose
    log "Installing Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose is already installed"
        docker-compose --version
    else
        # Get latest Docker Compose for ARM64
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
        curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        
        log_success "Docker Compose installed successfully"
    fi
    
    # Verify installation
    docker --version
    docker-compose --version
}

create_service_user() {
    log "Creating service user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        log_warning "User $SERVICE_USER already exists"
    else
        useradd -r -s /bin/bash -d /home/$SERVICE_USER -m $SERVICE_USER
        usermod -aG docker $SERVICE_USER
        log_success "Service user $SERVICE_USER created"
    fi
}

setup_directories() {
    log "Setting up directory structure..."
    
    # Create data directories
    mkdir -p "$DATA_DIR"/{postgres,backups,logs}
    mkdir -p /opt/automation-hub/{config,workspace}
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_USER /opt/automation-hub
    chmod -R 755 /opt/automation-hub
    
    # Create log directory
    mkdir -p /var/log/automation-hub
    chown $SERVICE_USER:$SERVICE_USER /var/log/automation-hub
    
    log_success "Directory structure created"
}

create_environment_files() {
    log "Creating environment configuration..."
    
    local env_file="/opt/automation-hub/.env"
    
    if [[ -f "$env_file" ]]; then
        log_warning "Environment file already exists at $env_file"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    # Generate random passwords
    local postgres_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    cat > "$env_file" << EOF
# AI Agent Automation Hub - Production Environment Configuration
# Generated on $(date)

# ======================
# REQUIRED CONFIGURATION
# ======================

# Discord Bot Token (REQUIRED - Get from Discord Developer Portal)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Database Configuration
POSTGRES_PASSWORD=$postgres_password
POSTGRES_PORT=5433

# ======================
# OPTIONAL CONFIGURATION
# ======================

# Discord Configuration
DISCORD_STATUS_CHANNEL_ID=
DISCORD_ALLOWED_GUILDS=
DISCORD_ADMIN_ROLE=Admin

# Integration Tokens
GITHUB_TOKEN=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Bot Behavior
BOT_MAX_CONCURRENT_TASKS=10
BOT_TASK_TIMEOUT_MINUTES=60
BOT_STATUS_UPDATE_INTERVAL=30
BOT_LOG_LEVEL=INFO

# Service Ports
BOT_HEALTH_PORT=8080
ORCHESTRATOR_PORT=8081
BACKEND_AGENT_PORT=8082
TESTING_AGENT_PORT=8083
MONITORING_PORT=9090

# Data Directory
DATA_DIR=$DATA_DIR

# Build Information
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION=latest
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')
EOF

    chown $SERVICE_USER:$SERVICE_USER "$env_file"
    chmod 600 "$env_file"
    
    log_success "Environment file created at $env_file"
    log_warning "IMPORTANT: Edit $env_file and set your Discord bot token!"
}

deploy_application() {
    log "Deploying application..."
    
    # Copy project files to deployment directory
    local deploy_dir="/opt/automation-hub/app"
    
    if [[ -d "$deploy_dir" ]]; then
        log "Backing up existing deployment..."
        mv "$deploy_dir" "$deploy_dir.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    mkdir -p "$deploy_dir"
    
    # Copy application files (excluding .git and other unnecessary files)
    rsync -av \
        --exclude='.git' \
        --exclude='.pytest_cache' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env*' \
        --exclude='venv' \
        --exclude='node_modules' \
        --exclude='data' \
        --exclude='logs/*.log' \
        "$PROJECT_DIR/" "$deploy_dir/"
    
    # Set ownership
    chown -R $SERVICE_USER:$SERVICE_USER "$deploy_dir"
    
    # Copy environment file
    cp /opt/automation-hub/.env "$deploy_dir/.env"
    
    log_success "Application deployed to $deploy_dir"
}

create_systemd_service() {
    log "Creating systemd service..."
    
    cat > /etc/systemd/system/automation-hub.service << EOF
[Unit]
Description=AI Agent Automation Hub
Requires=docker.service
After=docker.service
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/automation-hub/app
ExecStart=/usr/local/bin/docker-compose up -d --remove-orphans
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
User=$SERVICE_USER
Group=$SERVICE_USER
Environment=DOCKER_COMPOSE_FILE=docker-compose.yml

# Restart policy
Restart=on-failure
RestartSec=10

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/automation-hub

# Resource limits
MemoryLimit=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable automation-hub.service
    
    log_success "Systemd service created and enabled"
}

setup_monitoring() {
    log "Setting up monitoring configuration..."
    
    # Create Prometheus configuration
    cat > /opt/automation-hub/app/deploy/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'automation-hub'
    static_configs:
      - targets: ['discord-bot:8080', 'postgres:5432']
    metrics_path: '/health'
    scrape_interval: 30s

  - job_name: 'system'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 30s
EOF

    chown -R $SERVICE_USER:$SERVICE_USER /opt/automation-hub/app/deploy/
    
    log_success "Monitoring configuration created"
}

setup_backup_script() {
    log "Setting up backup script..."
    
    cat > /opt/automation-hub/backup.sh << 'EOF'
#!/bin/bash

# AI Agent Automation Hub Backup Script
set -e

BACKUP_DIR="/opt/automation-hub/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
POSTGRES_CONTAINER="automation_hub_postgres"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
log "Backing up PostgreSQL database..."
docker exec $POSTGRES_CONTAINER pg_dump -U automation automation_hub | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Backup configuration files
log "Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C /opt/automation-hub .env app/dev_bible

# Clean old backups (keep last 7 days)
log "Cleaning old backups..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

log "Backup completed successfully"
EOF

    chmod +x /opt/automation-hub/backup.sh
    chown $SERVICE_USER:$SERVICE_USER /opt/automation-hub/backup.sh
    
    # Create cron job for daily backups
    (crontab -u $SERVICE_USER -l 2>/dev/null; echo "0 2 * * * /opt/automation-hub/backup.sh >> /var/log/automation-hub/backup.log 2>&1") | crontab -u $SERVICE_USER -
    
    log_success "Backup script and cron job created"
}

configure_firewall() {
    log "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        # Configure UFW firewall
        ufw --force enable
        ufw default deny incoming
        ufw default allow outgoing
        
        # Allow SSH
        ufw allow ssh
        
        # Allow Discord bot health check port
        ufw allow 8080/tcp
        
        # Allow PostgreSQL (if external access needed)
        # ufw allow 5433/tcp
        
        # Allow monitoring (if needed)
        # ufw allow 9090/tcp
        
        log_success "Firewall configured"
    else
        log_warning "UFW not found, skipping firewall configuration"
    fi
}

health_check() {
    log "Performing health check..."
    
    cd /opt/automation-hub/app
    
    # Check if services are running
    local services=(postgres discord-bot)
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            all_healthy=false
        fi
    done
    
    # Check PostgreSQL connection
    if docker exec automation_hub_postgres pg_isready -U automation -d automation_hub &>/dev/null; then
        log_success "PostgreSQL is accessible"
    else
        log_error "PostgreSQL is not accessible"
        all_healthy=false
    fi
    
    # Check Discord bot health
    if curl -sf http://localhost:8080/health &>/dev/null; then
        log_success "Discord bot health check passed"
    else
        log_warning "Discord bot health check failed (may need Discord token)"
    fi
    
    if $all_healthy; then
        log_success "All core services are healthy"
        return 0
    else
        log_error "Some services are not healthy"
        return 1
    fi
}

print_next_steps() {
    echo
    echo "======================================"
    echo "🎉 AI Agent Automation Hub Setup Complete!"
    echo "======================================"
    echo
    echo "Next steps:"
    echo "1. Edit environment file: sudo nano /opt/automation-hub/.env"
    echo "2. Set your Discord bot token (DISCORD_BOT_TOKEN)"
    echo "3. Configure optional integration tokens (GitHub, Anthropic, etc.)"
    echo "4. Start the services: sudo systemctl start automation-hub"
    echo "5. Check status: sudo systemctl status automation-hub"
    echo "6. View logs: sudo journalctl -u automation-hub -f"
    echo
    echo "Useful commands:"
    echo "- Check services: cd /opt/automation-hub/app && docker-compose ps"
    echo "- View logs: cd /opt/automation-hub/app && docker-compose logs -f"
    echo "- Restart services: sudo systemctl restart automation-hub"
    echo "- Run backup: sudo -u $SERVICE_USER /opt/automation-hub/backup.sh"
    echo
    echo "Access URLs:"
    echo "- Bot health check: http://$(hostname -I | awk '{print $1}'):8080"
    echo "- Monitoring (if enabled): http://$(hostname -I | awk '{print $1}'):9090"
    echo
    echo "Data location: $DATA_DIR"
    echo "Logs location: /var/log/automation-hub/"
    echo "Service user: $SERVICE_USER"
    echo
}

main() {
    log "Starting AI Agent Automation Hub setup on Raspberry Pi 5"
    log "================================================================"
    
    # Checks
    check_root
    check_pi5
    
    # Setup steps
    update_system
    install_docker
    create_service_user
    setup_directories
    create_environment_files
    deploy_application
    create_systemd_service
    setup_monitoring
    setup_backup_script
    configure_firewall
    
    log "Setup completed successfully!"
    
    # Optional: Start services immediately
    read -p "Start services now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Starting services..."
        systemctl start automation-hub
        sleep 10
        health_check
    fi
    
    print_next_steps
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi