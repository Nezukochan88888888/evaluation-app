#!/usr/bin/env python3
"""
Quick Start Script for Flask Quiz Server
- One-click server startup
- Automatic database setup
- Network configuration
- Browser auto-launch
"""

import os
import sys
import sqlite3
import socket
import webbrowser
import time
from threading import Timer

def get_local_ip():
    """Get the local network IP address"""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "localhost"

def check_python_requirements():
    """Check if required modules are available"""
    required_modules = {
        'flask': 'flask',
        'flask_sqlalchemy': 'flask_sqlalchemy', 
        'flask_login': 'flask_login',
        'flask_admin': 'flask_admin',
        'flask_wtf': 'flask_wtf'
    }
    missing = []
    
    for display_name, import_name in required_modules.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(display_name)
    
    if missing:
        print(f"❌ Missing required modules: {', '.join(missing)}")
        print("Install with: pip install flask flask-sqlalchemy flask-login flask-admin flask-wtf")
        return False
    return True

def setup_database():
    """Initialize database and run migrations"""
    print("🔧 Setting up database...")
    
    try:
        # Import app after ensuring we're in the right directory
        sys.path.insert(0, os.getcwd())
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created/verified!")
            
        # Check for session_token migration
        if os.path.exists('app.db'):
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            try:
                cursor.execute("PRAGMA table_info(user)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'session_token' not in columns:
                    cursor.execute("ALTER TABLE user ADD COLUMN session_token VARCHAR(128)")
                    conn.commit()
                    print("✅ Database migration completed!")
                else:
                    print("✅ Database already up to date!")
                    
            except Exception as e:
                print(f"⚠️  Migration warning: {e}")
            finally:
                conn.close()
                
        return True
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def open_browser_delayed(url, delay=3):
    """Open browser after a delay"""
    def open_browser():
        print(f"🌐 Opening browser to {url}...")
        webbrowser.open(url)
    
    Timer(delay, open_browser).start()

def print_banner():
    """Print startup banner"""
    print("\n" + "="*50)
    print("🎓 FLASK QUIZ APP - QUICK START")
    print("="*50)

def print_access_info(local_ip, port=5000):
    """Print access information"""
    print(f"\n🚀 SERVER READY!")
    print("="*60)
    print(f"📱 STUDENT ACCESS:")
    print(f"   🌐 WiFi URL: http://{local_ip}:{port}")
    print(f"   💻 Local URL: http://localhost:{port}")
    print("")
    print(f"👨‍💼 ADMIN ACCESS:")
    print(f"   📊 Dashboard: http://{local_ip}:{port}/admin_dashboard")
    print(f"   👥 Students: http://{local_ip}:{port}/admin_students") 
    print(f"   ❓ Questions: http://{local_ip}:{port}/admin_questions")
    print(f"   ⚙️  Advanced: http://{local_ip}:{port}/admin")
    print("")
    print(f"📋 QUICK ADMIN GUIDE:")
    print(f"   🏠 Admin Dashboard - View overview & quick actions")
    print(f"   📊 Students Page - View scores, reset student progress")
    print(f"   📝 Questions Page - Add/edit quiz questions")
    print(f"   📤 Import Questions - Bulk upload via CSV/Excel")
    print("")
    print(f"📱 STUDENT SETUP:")
    print(f"   1️⃣  Students connect to same WiFi network")
    print(f"   2️⃣  Students open: http://{local_ip}:{port}")
    print(f"   3️⃣  Students register/login and take quiz")
    print("")
    print(f"⚠️  Press Ctrl+C to stop the server")
    print("="*60)

def main():
    """Main startup function"""
    print_banner()
    
    # Check Python requirements
    print("🔍 Checking Python requirements...")
    if not check_python_requirements():
        input("Press Enter to exit...")
        return
    print("✅ Python requirements satisfied!")
    
    # Setup database
    if not setup_database():
        input("Press Enter to exit...")
        return
    
    # Get network IP
    print("🌐 Getting network information...")
    local_ip = get_local_ip()
    print(f"✅ Network IP detected: {local_ip}")
    
    # Print access information
    print_access_info(local_ip)
    
    # Open admin dashboard automatically  
    open_browser_delayed(f"http://localhost:5000/admin_dashboard", delay=3)
    
    # Start the Flask server
    try:
        print("\n🎬 Starting Flask server...")
        
        # Import and run the app
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
    finally:
        print("\n👋 Thanks for using Flask Quiz App!")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()