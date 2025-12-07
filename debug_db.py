from app import app, db
from app.models import Questions, QuestionSet

with app.app_context():
    print("--- Question Sets ---")
    sets = QuestionSet.query.all()
    for s in sets:
        print(f"ID: {s.id}, Name: {s.name}, Category: {s.quiz_category}, Active: {s.is_active}")

    print("\n--- Questions Summary ---")
    questions = Questions.query.all()
    print(f"Total Questions: {len(questions)}")
    
    no_set = Questions.query.filter(Questions.question_set_id == None).count()
    print(f"Questions with NO Set (Default): {no_set}")
    
    for s in sets:
        count = Questions.query.filter_by(question_set_id=s.id).count()
        print(f"Questions in Set '{s.name}' (ID {s.id}): {count}")

    print("\n--- Questions in Active Sets ---")
    active_sets = QuestionSet.query.filter_by(is_active=True).all()
    for s in active_sets:
        qs = Questions.query.filter_by(question_set_id=s.id).all()
        print(f"Active Set '{s.name}' (ID {s.id}) contains IDs: {[q.q_id for q in qs]}")
