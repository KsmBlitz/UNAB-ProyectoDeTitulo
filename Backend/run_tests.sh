#!/bin/bash

# Script para ejecutar tests unitarios del backend
# Autor: Sistema de Monitoreo IoT
# Descripción: Ejecuta suite completa de tests con coverage

set -e  # Exit on error

echo "======================================"
echo "   Tests Unitarios - Backend IoT     "
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    source venv/bin/activate
fi

echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Install test dependencies if not present
echo "📦 Checking test dependencies..."
pip list | grep -q pytest || pip install pytest pytest-asyncio pytest-cov pytest-mock httpx faker
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Run tests based on argument
if [ "$1" = "coverage" ]; then
    echo "🧪 Running tests with coverage..."
    python3 -m pytest tests/ \
        --cov=app \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --cov-report=xml \
        -v \
        --tb=short \
        --color=yes
    
    echo ""
    echo -e "${GREEN}✅ Coverage report generated in htmlcov/index.html${NC}"
    
elif [ "$1" = "fast" ]; then
    echo "🧪 Running fast tests (no integration)..."
    python3 -m pytest tests/ \
        -v \
        --tb=short \
        --color=yes \
        -m "not integration"
    
elif [ "$1" = "specific" ]; then
    if [ -z "$2" ]; then
        echo -e "${RED}❌ Please provide test file or pattern${NC}"
        echo "Example: ./run_tests.sh specific test_auth_service.py"
        exit 1
    fi
    
    echo "🧪 Running specific tests: $2"
    python3 -m pytest tests/$2 \
        -v \
        --tb=short \
        --color=yes
    
elif [ "$1" = "watch" ]; then
    echo "👀 Running tests in watch mode..."
    python3 -m pytest tests/ \
        -v \
        --tb=short \
        --color=yes \
        -f  # Fail fast
    
else
    # Default: run all tests
    echo "🧪 Running all tests..."
    python3 -m pytest tests/ \
        -v \
        --tb=short \
        --color=yes \
        --maxfail=5  # Stop after 5 failures
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================"
    echo -e "   ✅ ALL TESTS PASSED! ✅           "
    echo -e "======================================${NC}"
else
    echo ""
    echo -e "${RED}======================================"
    echo -e "   ❌ SOME TESTS FAILED ❌          "
    echo -e "======================================${NC}"
    exit 1
fi
