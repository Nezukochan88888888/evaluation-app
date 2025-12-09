import sys
from app import app, db
from app.models import QuestionSet

def get_active_question_set(category):
    active_set = QuestionSet.query.filter_by(quiz_category=category, is_active=True).first()
    if active_set:
        return active_set
    return None

print("Running verification...")
with app.app_context():
    # Simulate: Viewing "All Sections"
    selected_section = 'All'
    
    # --- LOGIC FROM routes.py (Exact Copy) ---
    if selected_section != 'All':
        selected_set = get_active_question_set(selected_section)
    else:
        # If "All Sections" is selected, use active set for General
        selected_set = get_active_question_set('General')
        # Fallback: If no General set is active, check if ANY set is active (e.g. Midterm)
        # This ensures the banner appears even if the active exam is for a specific section
        if not selected_set:
            selected_set = QuestionSet.query.filter_by(is_active=True).first()
    # -----------------------------
            
    print(f"Scenario: Viewing 'All Sections'")
    print(f"Goal: Find ANY active question set if General is missing.")
    print(f"Result: Selected Set is '{selected_set.name if selected_set else 'None'}'")
    
    if selected_set and selected_set.is_active:
        print("SUCCESS: Found an active set to display.")
    else:
        print("FAILURE: No active set found.")
    
    sys.stdout.flush()
