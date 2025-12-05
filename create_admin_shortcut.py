#!/usr/bin/env python3
"""
Create Desktop Shortcut for Quiz Server - ADMIN VERSION
Creates an easy-to-use desktop shortcut that launches the admin interface directly
"""

import os
import sys
from pathlib import Path

def create_windows_shortcut():
    """Create a Windows desktop shortcut for admin"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # Get desktop path
        desktop = winshell.desktop()
        
        # Create shortcut path
        shortcut_path = os.path.join(desktop, "🎓 Quiz Server Admin.lnk")
        
        # Get current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Target the ADMIN_START.bat script
        target_path = os.path.join(current_dir, "ADMIN_START.bat")
        
        # Create shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = current_dir
        shortcut.Description = "Quiz Server - Admin Dashboard (One-click startup)"
        shortcut.save()
        
        print(f"✅ Admin desktop shortcut created: {shortcut_path}")
        return True
        
    except ImportError:
        print("❌ Advanced shortcut modules not found.")
        print("💡 Install with: pip install winshell pywin32")
        return False
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")
        return False

def create_batch_shortcut():
    """Create a simple batch file shortcut as fallback"""
    try:
        # Get desktop path
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Create batch file path
        batch_path = os.path.join(desktop, "🎓 Quiz Server Admin.bat")
        
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create batch content for admin
        batch_content = f'''@echo off
title Quiz Server - Admin Dashboard
echo.
echo 🎓 Starting Quiz Server Admin Dashboard...
echo.
cd /d "{current_dir}"
call ADMIN_START.bat
'''
        
        # Write batch file
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        print(f"✅ Admin desktop shortcut created: {batch_path}")
        print("💡 Double-click '🎓 Quiz Server Admin.bat' on your desktop to launch")
        return True
        
    except Exception as e:
        print(f"❌ Error creating batch shortcut: {e}")
        return False

def main():
    """Main function to create admin desktop shortcut"""
    print("=" * 60)
    print("🎓 QUIZ SERVER - ADMIN SHORTCUT CREATOR")
    print("=" * 60)
    print()
    
    if os.name == 'nt':  # Windows
        print("🖥️  Windows system detected")
        print("🔧 Creating admin desktop shortcut...")
        print()
        
        # Try advanced shortcut first, fallback to batch
        success = False
        if create_windows_shortcut():
            success = True
        elif create_batch_shortcut():
            success = True
        
        if success:
            print()
            print("🎉 SUCCESS! Admin shortcut created on desktop")
            print()
            print("📋 How to use:")
            print("   1. 👑 Double-click the admin shortcut on your desktop")
            print("   2. ✅ Server starts automatically with admin dashboard")
            print("   3. 🌐 Browser opens to admin interface")
            print("   4. 📱 Share student URL with your class")
            
        else:
            print()
            print("❌ Could not create shortcut automatically")
            print("💡 Manual options:")
            print("   • Double-click ADMIN_START.bat")
            print("   • Run: py quick_start.py")
            
    else:
        print("🐧 Non-Windows system detected")
        print("💡 Manual startup options:")
        print("   • Run: ./ADMIN_START.ps1")
        print("   • Run: python3 quick_start.py")
    
    print()
    print("📊 After starting, you'll have access to:")
    print("   🏠 Admin Dashboard - Overview & quick actions")
    print("   👥 Students Page - View scores, reset progress")
    print("   ❓ Questions Page - Add/edit quiz questions")
    print("   📤 Bulk Import - Upload questions via CSV/Excel")
    
    print()
    print("=" * 60)
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()