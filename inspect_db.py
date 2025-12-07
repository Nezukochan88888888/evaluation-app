from app import app, db
from app.models import User, Questions
import os

print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"DB Path should be: {os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')}")

try:
    with app.app_context():
        print("Inspecting tables...")
        engine = db.engine
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables found: {tables}")
        
        if 'user' in tables:
            print(f"User count: {User.query.count()}")
        if 'questions' in tables:
            print(f"Questions count: {Questions.query.count()}")
            
except Exception as e:
    print(f"Error: {e}")
