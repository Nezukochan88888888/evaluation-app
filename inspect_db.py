from app import app, db
from app.models import QuestionSet, Section, User

with app.app_context():
    print("--- Sections ---")
    sections = Section.query.all()
    for s in sections:
        print(f"ID: {s.id}, Name: {s.name}, Active: {s.is_active}")
        
    print("\n--- Question Sets ---")
    sets = QuestionSet.query.all()
    for s in sets:
        print(f"ID: {s.id}, Name: {s.name}, Category: {s.quiz_category}, Active: {s.is_active}")

    print("\n--- Users (Admins) ---")
    admins = User.query.filter_by(is_admin=True).all()
    for a in admins:
         print(f"User: {a.username}, Section: {a.section}")
