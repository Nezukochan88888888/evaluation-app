#!/usr/bin/env python3
"""
Creates desktop shortcuts for easy Flask Quiz Server access
"""

import os
import sys
from pathlib import Path

def create_windows_shortcut():
    """Create Windows desktop shortcut"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Flask Quiz Server.lnk")
        target = os.path.join(os.getcwd(), "quick_start.py")
        wDir = os.getcwd()
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()
        
        print(f"✅ Desktop shortcut created: {path}")
        return True
    except ImportError:
        print("⚠️  Windows shortcut creation requires: pip install winshell pywin32")
        return False
    except Exception as e:
        print(f"❌ Error creating Windows shortcut: {e}")
        return False

def create_batch_shortcut():
    """Create simple batch file shortcut"""
    desktop_path = Path.home() / "Desktop"
    if not desktop_path.exists():
        desktop_path = Path.home()
    
    shortcut_path = desktop_path / "Start Quiz Server.bat"
    
    batch_content = f'''@echo off
cd /d "{os.getcwd()}"
python quick_start.py
pause
'''
    
    try:
        with open(shortcut_path, 'w') as f:
            f.write(batch_content)
        print(f"✅ Batch shortcut created: {shortcut_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating batch shortcut: {e}")
        return False

def main():
    """Create desktop shortcuts"""
    print("🔗 Creating Desktop Shortcuts for Flask Quiz Server")
    print("=" * 50)
    
    if os.name == 'nt':  # Windows
        print("🪟 Windows detected - creating shortcuts...")
        
        # Try advanced Windows shortcut first
        if not create_windows_shortcut():
            # Fallback to batch file
            create_batch_shortcut()
    else:  # Linux/Mac
        print("🐧 Unix-like system detected")
        print("You can run the server with: python3 quick_start.py")
    
    print("\n🎉 Setup complete!")
    print("\nYou now have these easy ways to start the server:")
    print("1. Double-click the desktop shortcut")
    print("2. Run: python quick_start.py")
    print("3. Run: start_quiz_server.bat (Windows)")
    print("4. Run: ./start_quiz_server.ps1 (PowerShell)")

if __name__ == "__main__":
    main()