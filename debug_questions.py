from app import app, db
from app.models import Questions

with app.app_context():
    print("--- Latest Questions ---")
    questions = Questions.query.order_by(Questions.q_id.desc()).limit(5).all()
    for q in questions:
        print(f"ID: {q.q_id}, Text: {q.ques[:50]}..., Set ID: {q.question_set_id}, Category: {q.quiz_category}")
