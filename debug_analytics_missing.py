from app import app, db
from app.models import Questions, QuestionSet, StudentResponse

with app.app_context():
    print("--- Categories & Active Sets ---")
    categories = db.session.query(QuestionSet.quiz_category).distinct().all()
    categories = [c[0] for c in categories]
    
    for cat in categories:
        active_set = QuestionSet.query.filter_by(quiz_category=cat, is_active=True).first()
        print(f"Category: '{cat}'")
        if active_set:
            print(f"  Active Set: '{active_set.name}' (ID: {active_set.id})")
            # Count questions in this set
            q_count = Questions.query.filter_by(question_set_id=active_set.id).count()
            print(f"  Questions in Set: {q_count}")
            
            # Count responses for this set
            r_count = StudentResponse.query.filter_by(question_set_id=active_set.id).count()
            print(f"  Responses for Set: {r_count}")
        else:
            print("  Active Set: None")
            q_count = Questions.query.filter_by(quiz_category=cat).count()
            print(f"  Questions in Category (Total): {q_count}")

    print("\n--- Questions Check ---")
    # List all questions and their sets
    questions = Questions.query.all()
    for q in questions:
        print(f"QID: {q.q_id}, SetID: {q.question_set_id}, Category: {q.quiz_category}")
