#!/bin/bash

# Alphalens Autonomous Trading System - Setup Script

set -e

echo "========================================"
echo "Alphalens Setup Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✓ Created logs directory${NC}"

# Install base Alphalens dependencies
echo ""
echo "Installing base Alphalens dependencies..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Base dependencies installed${NC}"

# Install agent system dependencies
echo ""
echo "Installing agent system dependencies..."
pip install -q -r requirements-agents.txt
echo -e "${GREEN}✓ Agent dependencies installed${NC}"

# Set up environment file
if [ ! -f .env ]; then
    echo ""
    echo "Setting up .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your ANTHROPIC_API_KEY${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Check for PostgreSQL
echo ""
echo "Checking PostgreSQL..."
if pg_isready -h localhost -p 5432 &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL is not running${NC}"
    echo "  Options:"
    echo "  1. Start local PostgreSQL: sudo systemctl start postgresql"
    echo "  2. Use Docker Compose: docker-compose up -d postgres"
fi

# Check for Redis
echo ""
echo "Checking Redis..."
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis is not running${NC}"
    echo "  Options:"
    echo "  1. Start local Redis: sudo systemctl start redis"
    echo "  2. Use Docker Compose: docker-compose up -d redis"
fi

# Create database
echo ""
echo "Setting up database..."
if pg_isready -h localhost -p 5432 &> /dev/null; then
    if psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw alphalens_agents; then
        echo -e "${GREEN}✓ Database 'alphalens_agents' already exists${NC}"
    else
        echo "Creating database..."
        createdb -h localhost -U postgres alphalens_agents 2>/dev/null || echo -e "${YELLOW}Note: May need PostgreSQL password${NC}"
    fi
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY"
echo "2. Ensure PostgreSQL and Redis are running"
echo "3. Run: python example_usage.py"
echo ""
