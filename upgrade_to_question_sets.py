from app import app, db
from app.models import Questions, QuizScore, StudentResponse, QuestionSet

def upgrade_data():
    with app.app_context():
        print("Starting Data Migration to Question Sets...")
        
        # 1. Get all unique categories
        categories = db.session.query(Questions.quiz_category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        print(f"Found categories: {categories}")
        
        for category in categories:
            print(f"Processing category: {category}")
            
            # Check if set exists
            q_set = QuestionSet.query.filter_by(quiz_category=category, name="Standard Set").first()
            
            if not q_set:
                q_set = QuestionSet(
                    name="Standard Set",
                    quiz_category=category,
                    is_active=True,
                    description=f"Default question set for {category}"
                )
                db.session.add(q_set)
                db.session.commit() # Commit to get ID
                print(f"Created QuestionSet: {q_set}")
            else:
                print(f"Using existing QuestionSet: {q_set}")
                
            # Update Questions
            q_count = Questions.query.filter_by(quiz_category=category).update(
                {Questions.question_set_id: q_set.id}, synchronize_session=False
            )
            print(f"Updated {q_count} questions.")
            
            # Update QuizScore
            s_count = QuizScore.query.filter_by(quiz_category=category).update(
                {QuizScore.question_set_id: q_set.id}, synchronize_session=False
            )
            print(f"Updated {s_count} quiz scores.")
            
            # Update StudentResponse
            r_count = StudentResponse.query.filter_by(quiz_category=category).update(
                {StudentResponse.question_set_id: q_set.id}, synchronize_session=False
            )
            print(f"Updated {r_count} student responses.")
            
        db.session.commit()
        print("Data Migration Complete.")

if __name__ == "__main__":
    upgrade_data()
