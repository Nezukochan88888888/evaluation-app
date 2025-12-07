from app import app, db
from app.models import QuestionSet

with app.app_context():
    # Find Standard Set
    std_set = QuestionSet.query.filter_by(name="Standard Set", quiz_category="General").first()
    if std_set:
        print(f"Found Standard Set (ID {std_set.id}). Activating...")
        
        # Deactivate others in General
        QuestionSet.query.filter_by(quiz_category="General").update({QuestionSet.is_active: False})
        
        # Activate Standard Set
        std_set.is_active = True
        db.session.commit()
        print("Standard Set Activated.")
    else:
        print("Standard Set not found.")
