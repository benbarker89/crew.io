#!/bin/bash

# Legal Case Management System - Startup Script

echo "=========================================="
echo "Legal Case Management System"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Initialize database if it doesn't exist
if [ ! -f "database/legal_cases.db" ]; then
    echo "Initializing database..."
    cd backend
    python3 models.py
    cd ..
    echo ""
fi

# Start the server
echo "Starting server..."
echo ""
echo "=========================================="
echo "Access the application at:"
echo "  Dashboard: http://localhost:8000/frontend/index.html"
echo "  API Docs:  http://localhost:8000/docs"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python3 main.py
