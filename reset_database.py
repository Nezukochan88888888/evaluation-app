#!/usr/bin/env python3
"""
Database Reset Script for Quiz Application
Resets the database to use the new Questions model with enhanced fields
"""

import os
import sqlite3
from app import app, db
from app.models import User, Questions, QuizScore

def reset_database():
    """Complete database reset with new schema"""
    print("=" * 60)
    print("DATABASE RESET - Educational Content Upgrade")
    print("=" * 60)
    
    # 1. Backup existing database
    if os.path.exists('app.db'):
        backup_name = f'app_backup_{int(__import__("time").time())}.db'
        import shutil
        shutil.copy2('app.db', backup_name)
        print(f"✓ Existing database backed up to: {backup_name}")
    
    # 2. Delete old database
    if os.path.exists('app.db'):
        os.remove('app.db')
        print("✓ Old database deleted")
    
    # 3. Create new database with updated schema
    with app.app_context():
        db.create_all()
        print("✓ New database created with enhanced schema")
        
        # 4. Create default admin user
        admin_user = User(username='admin', email='admin@quiz.local', is_admin=True)
        admin_user.set_password('admin123')  # Change this password!
        db.session.add(admin_user)
        
        # 5. Add sample question with new fields
        sample_question = Questions(
            q_id=1,
            ques="What is the capital of France?",
            a="London",
            b="Berlin", 
            c="Paris",
            d="Madrid",
            ans="Paris",
            quiz_category="Geography",
            time_limit=60,
            # NEW MODULE 1 FIELDS:
            rationalization="Paris is the capital and largest city of France, located in the north-central part of the country along the Seine River.",
            points=1,
            category="Geography",
            media_path=None
        )
        db.session.add(sample_question)
        
        try:
            db.session.commit()
            print("✓ Sample admin user and question created")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating sample data: {e}")
    
    print("\n" + "=" * 60)
    print("DATABASE RESET COMPLETE!")
    print("=" * 60)
    print("Default Admin Login:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
    print("=" * 60)
    print("New Features Available:")
    print("✓ Module 1: Enhanced question fields (rationalization, points, category, media)")
    print("✓ Module 2: Admin forms updated for new fields")  
    print("✓ Module 3: Analytics dashboard with distractor analysis")
    print("✓ Module 4: Student feedback with explanations for wrong answers")
    print("=" * 60)

if __name__ == "__main__":
    reset_database()