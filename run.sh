#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}SEMrush Data Processor${NC}"
echo -e "${BLUE}======================${NC}\n"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}UV is not installed. Installing now...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}UV installed successfully!${NC}"
    echo -e "${YELLOW}Please restart your terminal and run this script again.${NC}"
    exit 0
fi

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo -e "${YELLOW}Error: pyproject.toml not found!${NC}"
    exit 1
fi

# Sync dependencies
echo -e "${BLUE}Installing/updating dependencies...${NC}"
uv sync

# Create uploads directory
mkdir -p uploads

# Check for command line arguments
MODE=${1:-dev}

if [ "$MODE" == "dev" ] || [ "$MODE" == "development" ]; then
    echo -e "\n${GREEN}Starting Flask development server...${NC}"
    echo -e "${BLUE}Access the application at: http://127.0.0.1:5000${NC}\n"
    uv run flask run --debug
elif [ "$MODE" == "prod" ] || [ "$MODE" == "production" ]; then
    echo -e "\n${GREEN}Starting production server with Gunicorn...${NC}"
    
    if ! uv pip show gunicorn &> /dev/null; then
        echo -e "${YELLOW}Gunicorn not found. Installing...${NC}"
        uv add gunicorn
    fi
    
    echo -e "${BLUE}Access the application at: http://127.0.0.1:8000${NC}\n"
    uv run gunicorn -w 4 -b 0.0.0.0:8000 app:app
else
    echo -e "${YELLOW}Invalid mode: $MODE${NC}"
    echo -e "Usage: ./run.sh [dev|prod]"
    exit 1
fi
