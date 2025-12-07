from app import app, db
from app.models import QuestionSet

with app.app_context():
    sets = QuestionSet.query.all()
    for s in sets:
        print(f"ID: {s.id}, Name: '{s.name}', Category: '{s.quiz_category}', Active: {s.is_active}")
