from app import app, db
from sqlalchemy import text
from app.models import Section, User

with app.app_context():
    with db.engine.connect() as conn:
        try:
            # 1. Create Section Table
            print("Creating 'section' table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS section (
                    id INTEGER PRIMARY KEY, 
                    name VARCHAR(64) UNIQUE NOT NULL
                )
            """))
            print("✅ 'section' table created.")
            
            # 2. Add section_id to User (if not exists)
            print("Adding 'section_id' to 'user' table...")
            try:
                conn.execute(text("ALTER TABLE user ADD COLUMN section_id INTEGER REFERENCES section(id)"))
                print("✅ 'section_id' column added.")
            except Exception as e:
                print(f"ℹ️  Column 'section_id' might already exist: {e}")

            # 3. Migrate data (String -> ID)
            print("Migrating existing sections...")
            # Use SQLAlchemy ORM for this to simplify logic
            
        except Exception as e:
            print(f"❌ Database Schema Error: {e}")

    # ORM Migration Logic
    try:
        # Find all unique string sections
        users = User.query.filter(User.section.isnot(None), User.section != 'Default').all()
        unique_section_names = set(u.section for u in users if u.section)
        
        print(f"Found existing sections: {unique_section_names}")
        
        section_map = {}
        for name in unique_section_names:
            # Check if exists
            sect = Section.query.filter_by(name=name).first()
            if not sect:
                sect = Section(name=name)
                db.session.add(sect)
                db.session.commit() # Commit to get ID
            section_map[name] = sect.id
            
        # Update Users
        count = 0
        for user in users:
            if user.section in section_map:
                user.section_id = section_map[user.section]
                count += 1
        
        db.session.commit()
        print(f"✅ Migrated {count} users to new Section table.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Data Migration Error: {e}")
