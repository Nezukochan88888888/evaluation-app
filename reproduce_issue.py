from app import app, db
from app.models import QuestionSet, Questions, User
from app.routes import get_active_question_set

with app.app_context():
    # 1. Create a new set "Test Set" in "General"
    print("Creating 'Test Set'...")
    test_set = QuestionSet.query.filter_by(name="Test Set").first()
    if not test_set:
        test_set = QuestionSet(name="Test Set", quiz_category="General", is_active=False)
        db.session.add(test_set)
        db.session.commit()
    print(f"Test Set ID: {test_set.id}")

    # 2. Add a question to it
    print("Adding Question to Test Set...")
    q = Questions.query.filter_by(ques="Test Question 123").first()
    if not q:
        q = Questions(
            q_id=999,
            ques="Test Question 123",
            a="A", b="B", c="C", d="D", ans="A",
            quiz_category="General",
            question_set_id=test_set.id
        )
        db.session.add(q)
        db.session.commit()
    else:
        q.question_set_id = test_set.id
        db.session.commit()
    
    # 3. Simulate Toggle: Activate "Test Set"
    print("Activating 'Test Set'...")
    # Deactivate others in General
    QuestionSet.query.filter_by(quiz_category="General").update({QuestionSet.is_active: False})
    test_set.is_active = True
    db.session.commit()

    # 4. Verify Active Set
    print("\n--- Verifying Active Set for 'General' ---")
    active_set = get_active_question_set("General")
    if active_set:
        print(f"Active Set is: {active_set.name} (ID {active_set.id})")
    else:
        print("No Active Set found!")

    # 5. Verify Questions found for this set
    if active_set:
        qs = Questions.query.filter_by(question_set_id=active_set.id).all()
        print(f"Questions in active set: {[q.q_id for q in qs]}")
        
        # Check if 999 is there
        if 999 in [q.q_id for q in qs]:
            print("SUCCESS: Test Question 123 is in the active set.")
        else:
            print("FAILURE: Test Question 123 NOT found in active set.")
            
    # 6. Check 'Standard Set' status
    std_set = QuestionSet.query.filter_by(name="Standard Set").first()
    if std_set:
        print(f"'Standard Set' Active Status: {std_set.is_active}")
