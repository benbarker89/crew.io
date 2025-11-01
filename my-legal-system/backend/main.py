"""
Main entry point for Legal Case Management System
"""
import uvicorn
from models import init_db

if __name__ == "__main__":
    # Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")

    # Run FastAPI server
    print("\nStarting Legal Case Management System...")
    print("=" * 60)
    print("Server running at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Dashboard: http://localhost:8000/dashboard")
    print("=" * 60)

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
