from app import app, db
from app.models import QuestionSet, Section

def get_active_question_set(category):
    active_set = QuestionSet.query.filter_by(quiz_category=category, is_active=True).first()
    if active_set:
        return active_set
    return None

with app.app_context():
    print("--- Simulation: Default State ---")
    # Current DB state: Midterm (Euclid) is active. Standard (General) is inactive.
    
    selected_section = 'All'
    if selected_section != 'All':
        selected_set = get_active_question_set(selected_section)
    else:
        selected_set = get_active_question_set('General')
        
    print(f"Selected Section: {selected_section}")
    print(f"Selected Set: {selected_set.name if selected_set else 'None'}")
    
    print("\n--- Simulation: Standard Set Active ---")
    # Activate Standard Set
    std_set = QuestionSet.query.filter_by(name='Standard Set').first()
    if std_set:
        std_set.is_active = True
        db.session.commit()
    
    selected_section = 'All'
    if selected_section != 'All':
        selected_set = get_active_question_set(selected_section)
    else:
        selected_set = get_active_question_set('General')
        
    print(f"Selected Section: {selected_section}")
    print(f"Selected Set: {selected_set.name if selected_set else 'None'}")
    
    # Clean up (Deactivate Standard Set)
    if std_set:
        std_set.is_active = False
        db.session.commit()
    
    print("\n--- Simulation: Viewing Euclid Section ---")
    selected_section = 'Euclid'
    if selected_section != 'All':
        selected_set = get_active_question_set(selected_section)
    else:
        selected_set = get_active_question_set('General')
        
    print(f"Selected Section: {selected_section}")
    print(f"Selected Set: {selected_set.name if selected_set else 'None'}")
    
