#!/usr/bin/env python3
"""
Ghuntred-v2 Real System Startup Script
Initializes database and starts the real application
"""

import os
import sys
import asyncio
import subprocess
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ██╗  ██╗██╗   ██╗███╗   ██╗████████╗██████╗ ███████╗██████╗ ®            ║
║    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔══██╗██╔════╝██╔══██╗             ║
║    ███████║██║   ██║██╔██╗ ██║   ██║   ██████╔╝█████╗  ██║  ██║             ║
║    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══██╗██╔══╝  ██║  ██║             ║
║    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ██║  ██║███████╗██████╔╝             ║
║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═════╝              ║
║                                                                              ║
║                    REAL HR TECHNOLOGY PLATFORM v2.0                         ║
║                         with Database Integration                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import sqlalchemy
        import psycopg2
        import redis
        print("✅ Core dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")

def check_database():
    """Check database connection"""
    print("🔍 Checking database connection...")
    
    try:
        from src.database.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and credentials are correct")
        return False

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up environment...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("📄 Creating .env file from template...")
        example_file = Path(".env.example")
        if example_file.exists():
            env_file.write_text(example_file.read_text())
            print("✅ .env file created - please configure your settings")
        else:
            print("❌ .env.example not found")
    else:
        print("✅ .env file found")

async def initialize_database():
    """Initialize database with sample data"""
    print("🗄️ Initializing database...")
    
    try:
        from src.init_database import init_database
        await init_database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_application():
    """Start the FastAPI application"""
    print("🚀 Starting Ghuntred-v2 Real Application...")
    
    try:
        import uvicorn
        from src.main_real import app
        
        print("🌐 Application will be available at:")
        print("   • API Documentation: http://localhost:8000/docs")
        print("   • Health Check: http://localhost:8000/health")
        print("   • Company Dashboard: http://localhost:8000/api/v1/company/huntred_mx/dashboard")
        print("   • Employees API: http://localhost:8000/api/v1/companies/huntred_mx/employees")
        print()
        print("💬 WhatsApp Bot Test:")
        print("   • POST http://localhost:8000/api/v1/webhooks/whatsapp/huntred_mx")
        print("   • Test phones: +525512345678, +525587654321")
        print()
        print("🔄 Press Ctrl+C to stop the server")
        print("=" * 80)
        
        uvicorn.run(
            "src.main_real:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🔄 Shutting down Ghuntred-v2...")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

async def main():
    """Main startup sequence"""
    print_banner()
    
    print("🚀 Starting Ghuntred-v2 Real System...")
    print("=" * 80)
    
    # Step 1: Check dependencies
    check_dependencies()
    
    # Step 2: Setup environment
    setup_environment()
    
    # Step 3: Check database
    if not check_database():
        print("\n❌ Cannot proceed without database connection")
        print("💡 Please ensure PostgreSQL is running and configure DATABASE_URL in .env")
        return
    
    # Step 4: Initialize database
    print("\n" + "=" * 80)
    user_input = input("🗄️ Do you want to initialize/reset the database? (y/N): ")
    if user_input.lower() in ['y', 'yes']:
        if not await initialize_database():
            print("❌ Database initialization failed")
            return
    
    # Step 5: Start application
    print("\n" + "=" * 80)
    start_application()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        sys.exit(1)