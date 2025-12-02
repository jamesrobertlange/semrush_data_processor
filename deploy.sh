#!/bin/bash

# SEMrush Data Processor - Production Deployment Script
# Run this script on your VPS to set up the application

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_DIR="/var/www/semrush-processor"
LOG_DIR="/var/log/semrush-processor"
SERVICE_NAME="semrush-processor"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}SEMrush Data Processor Deployment${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Step 1: System dependencies
echo -e "${YELLOW}[1/8] Installing system dependencies...${NC}"
apt update
apt install -y python3 python3-pip git curl build-essential nginx

# Step 2: Install UV
echo -e "${YELLOW}[2/8] Installing UV package manager...${NC}"
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo -e "${GREEN}✓ UV installed${NC}"
else
    echo -e "${GREEN}✓ UV already installed${NC}"
fi

# Step 3: Create directories
echo -e "${YELLOW}[3/8] Creating application directories...${NC}"
mkdir -p "$APP_DIR"
mkdir -p "$LOG_DIR"
mkdir -p /tmp/semrush_uploads
chmod 755 "$LOG_DIR"
echo -e "${GREEN}✓ Directories created${NC}"

# Step 4: Application setup
echo -e "${YELLOW}[4/8] Setting up application...${NC}"

# Clone or pull repository
if [ -d "$APP_DIR/.git" ]; then
    echo -e "${BLUE}Updating existing repository...${NC}"
    cd "$APP_DIR"
    git pull
else
    echo -e "${BLUE}Cloning repository...${NC}"
    rm -rf "$APP_DIR"
    git clone https://github.com/jamesrobertlange/semrush_data_processor.git "$APP_DIR"
    cd "$APP_DIR"
fi

if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found${NC}"
    exit 1
fi

# Replace app.py with production version if it exists
if [ -f "app_production.py" ]; then
    echo -e "${BLUE}Using production app.py...${NC}"
    mv app.py app_original.py.bak 2>/dev/null || true
    mv app_production.py app.py
fi

# Install dependencies
/root/.cargo/bin/uv sync
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 5: Generate secret key
echo -e "${YELLOW}[5/8] Generating secret key...${NC}"
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
echo -e "${GREEN}✓ Secret key generated${NC}"

# Step 6: Configure systemd service
echo -e "${YELLOW}[6/8] Configuring systemd service...${NC}"

if [ -f "semrush-processor.service" ]; then
    # Update SECRET_KEY in service file
    sed -i "s/CHANGE_THIS_TO_RANDOM_STRING/$SECRET_KEY/" semrush-processor.service
    
    cp semrush-processor.service /etc/systemd/system/
    systemctl daemon-reload
    echo -e "${GREEN}✓ Systemd service configured${NC}"
else
    echo -e "${YELLOW}⚠ semrush-processor.service not found, skipping...${NC}"
fi

# Step 7: Configure Nginx (optional)
echo -e "${YELLOW}[7/8] Nginx configuration...${NC}"
read -p "Do you want to configure Nginx as reverse proxy? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "nginx-semrush-processor.conf" ]; then
        cp nginx-semrush-processor.conf /etc/nginx/sites-available/semrush-processor
        ln -sf /etc/nginx/sites-available/semrush-processor /etc/nginx/sites-enabled/
        
        # Test nginx configuration
        nginx -t
        if [ $? -eq 0 ]; then
            systemctl restart nginx
            echo -e "${GREEN}✓ Nginx configured and restarted${NC}"
        else
            echo -e "${RED}✗ Nginx configuration test failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ nginx-semrush-processor.conf not found${NC}"
    fi
else
    echo -e "${YELLOW}⊘ Skipping Nginx configuration${NC}"
fi

# Step 8: Start the service
echo -e "${YELLOW}[8/8] Starting the application...${NC}"
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Wait a moment for service to start
sleep 2

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
    
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${BLUE}======================================${NC}\n"
    
    echo -e "${YELLOW}Access your application at:${NC}"
    echo -e "  • Direct: ${BLUE}http://104.168.107.216:8000${NC}"
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "  • Via Nginx: ${BLUE}http://104.168.107.216${NC}"
    fi
    
    echo -e "\n${YELLOW}Useful commands:${NC}"
    echo -e "  • Check status:  ${BLUE}systemctl status $SERVICE_NAME${NC}"
    echo -e "  • View logs:     ${BLUE}tail -f $LOG_DIR/error.log${NC}"
    echo -e "  • Restart:       ${BLUE}systemctl restart $SERVICE_NAME${NC}"
    echo -e "  • Stop:          ${BLUE}systemctl stop $SERVICE_NAME${NC}"
    
    echo -e "\n${YELLOW}Log files:${NC}"
    echo -e "  • Access: $LOG_DIR/access.log"
    echo -e "  • Errors: $LOG_DIR/error.log"
    
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo -e "${YELLOW}Check logs: journalctl -u $SERVICE_NAME -n 50${NC}"
    exit 1
fi