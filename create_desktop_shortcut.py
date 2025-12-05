#!/usr/bin/env python3
"""
Create desktop shortcuts for Quiz Server Control System
Enhanced with easy switch on/off functionality
"""

import os
import sys
from pathlib import Path

def create_windows_shortcuts():
    """Create Windows desktop shortcuts using winshell"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        script_dir = os.getcwd()
        shell = Dispatch('WScript.Shell')
        
        # Enhanced shortcuts for server control
        shortcuts = [
            {
                'name': '🚀 Start Quiz Server',
                'target': os.path.join(script_dir, 'QUICK_START.bat'),
                'description': 'Quick start the quiz server'
            },
            {
                'name': '⛔ Stop Quiz Server', 
                'target': os.path.join(script_dir, 'QUICK_STOP.bat'),
                'description': 'Quick stop the quiz server'
            },
            {
                'name': '🎯 Quiz Server Control',
                'target': os.path.join(script_dir, 'SERVER_CONTROL.bat'),
                'description': 'Full server control panel'
            },
            {
                'name': '📊 Server Status',
                'target': os.path.join(script_dir, 'SERVER_STATUS.bat'),
                'description': 'Check server status and access links'
            }
        ]
        
        for shortcut_info in shortcuts:
            shortcut_path = os.path.join(desktop, f"{shortcut_info['name']}.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = shortcut_info['target']
            shortcut.WorkingDirectory = script_dir
            shortcut.Description = shortcut_info['description']
            shortcut.save()
            print(f"✅ Created: {shortcut_info['name']}.lnk")
        
        return True
        
    except ImportError:
        print("⚠️  Advanced shortcuts require: pip install winshell pywin32")
        return False
    except Exception as e:
        print(f"❌ Error creating Windows shortcuts: {e}")
        return False

def create_batch_shortcuts():
    """Create simple batch file shortcuts"""
    desktop_path = Path.home() / "Desktop"
    if not desktop_path.exists():
        desktop_path = Path.home()
    
    script_dir = os.getcwd()
    
    shortcuts = [
        {
            'name': '🚀 Start Quiz Server',
            'target': 'QUICK_START.bat',
            'description': 'Quick start the quiz server'
        },
        {
            'name': '⛔ Stop Quiz Server', 
            'target': 'QUICK_STOP.bat',
            'description': 'Quick stop the quiz server'
        },
        {
            'name': '🎯 Quiz Server Control',
            'target': 'SERVER_CONTROL.bat',
            'description': 'Full server control panel'
        },
        {
            'name': '📊 Server Status',
            'target': 'SERVER_STATUS.bat',
            'description': 'Check server status'
        }
    ]
    
    success = True
    
    for shortcut_info in shortcuts:
        shortcut_path = desktop_path / f"{shortcut_info['name']}.bat"
        batch_content = f'''@echo off
title {shortcut_info['description']}
cd /d "{script_dir}"
call "{shortcut_info['target']}"
'''
        
        try:
            with open(shortcut_path, 'w') as f:
                f.write(batch_content)
            print(f"✅ Created: {shortcut_info['name']}.bat")
        except Exception as e:
            print(f"❌ Error creating {shortcut_info['name']}: {e}")
            success = False
    
    return success

def create_start_menu_shortcuts():
    """Create Start Menu shortcuts for Windows"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        programs = winshell.programs()
        quiz_folder = os.path.join(programs, "Quiz Server Control")
        
        if not os.path.exists(quiz_folder):
            os.makedirs(quiz_folder)
        
        shell = Dispatch('WScript.Shell')
        script_dir = os.getcwd()
        
        shortcuts = [
            ('Quiz Server Control Panel', 'SERVER_CONTROL.bat'),
            ('Start Quiz Server', 'QUICK_START.bat'),
            ('Stop Quiz Server', 'QUICK_STOP.bat'),
            ('Server Status', 'SERVER_STATUS.bat'),
            ('PowerShell Control', 'server-control.ps1')
        ]
        
        for name, target in shortcuts:
            shortcut = shell.CreateShortCut(os.path.join(quiz_folder, f"{name}.lnk"))
            if target.endswith('.ps1'):
                shortcut.Targetpath = 'powershell.exe'
                shortcut.Arguments = f'-ExecutionPolicy Bypass -File "{os.path.join(script_dir, target)}"'
            else:
                shortcut.Targetpath = os.path.join(script_dir, target)
            shortcut.WorkingDirectory = script_dir
            shortcut.save()
        
        print(f"✅ Start Menu shortcuts created in: {quiz_folder}")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not create Start Menu shortcuts: {e}")
        return False

def main():
    """Create all shortcuts for Quiz Server Control System"""
    print("🔗 CREATING QUIZ SERVER CONTROL SHORTCUTS")
    print("=========================================")
    print()
    print("This will create easy-access shortcuts for:")
    print("• 🚀 Starting the server instantly")
    print("• ⛔ Stopping the server safely") 
    print("• 🎯 Full control panel access")
    print("• 📊 Quick status checking")
    print()
    
    if os.name == 'nt':  # Windows
        print("🪟 Windows detected - creating enhanced shortcuts...")
        print()
        
        # Try advanced Windows shortcuts first
        if create_windows_shortcuts():
            print("\n🎉 Professional .lnk shortcuts created!")
            
            # Also try Start Menu shortcuts
            print("\n📁 Creating Start Menu shortcuts...")
            create_start_menu_shortcuts()
            
        else:
            # Fallback to batch shortcuts
            print("📝 Creating fallback batch shortcuts...")
            create_batch_shortcuts()
        
    else:  # Linux/Mac
        print("🐧 Unix-like system detected")
        print("Manual commands available:")
        print("• Start: ./QUICK_START.bat")
        print("• Stop: ./QUICK_STOP.bat") 
        print("• Control: ./SERVER_CONTROL.bat")
        print("• PowerShell: pwsh server-control.ps1")
    
    print()
    print("🎊 SHORTCUT CREATION COMPLETE!")
    print("==============================")
    print()
    print("📂 Check your Desktop for these shortcuts:")
    print("  🚀 Start Quiz Server      - One-click start")
    print("  ⛔ Stop Quiz Server       - One-click stop")
    print("  🎯 Quiz Server Control    - Full management")
    print("  📊 Server Status          - Quick status check")
    print()
    print("🌐 After starting, access via:")
    print("  👥 Students: http://localhost:5000")
    print("  👨‍💼 Admin: http://localhost:5000/admin_dashboard")
    print("  📋 Login: admin / admin123")

if __name__ == "__main__":
    main()