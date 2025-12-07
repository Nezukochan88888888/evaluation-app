from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE user ADD COLUMN section VARCHAR(64) DEFAULT 'Default'"))
            print("✅ Successfully added 'section' column to User table.")
        except Exception as e:
            print(f"⚠️  Could not add column (it might already exist): {e}")
