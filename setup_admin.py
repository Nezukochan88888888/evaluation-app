from app import app, db
from app.models import User
import sys
import os

sys.path.insert(0, os.getcwd())

with app.app_context():
    try:
        u = User.query.filter_by(username='admin').first()
        if not u:
            u = User(username='admin', email='admin@local.test', is_admin=True)
            u.set_password('admin')
            db.session.add(u)
            print("Created new admin user.")
        else:
            u.is_admin = True
            u.set_password('admin')
            print("Updated existing admin user.")
            
        db.session.commit()
        print("SUCCESS: User 'admin' with password 'admin' is ready.")
    except Exception as e:
        print(f"ERROR: {e}")
