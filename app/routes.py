from app import app, db, admin
from flask import render_template, request, redirect, url_for, session, g, flash, make_response
try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlparse as url_parse
from werkzeug.utils import secure_filename
from app.forms import LoginForm, RegistrationForm, QuestionForm, AdminQuestionForm, EditQuestionForm
from app.models import User, Questions, QuizScore
from sqlalchemy import desc
from flask_login import current_user, login_user, logout_user, login_required
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
from functools import wraps
import csv
import io
import secrets
import time
import os
from datetime import datetime


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class BulkUploadView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if not (current_user.is_authenticated and getattr(current_user, 'is_admin', False)):
            return redirect(url_for('login', next=request.url))
        if request.method == 'POST':
            file = request.files.get('file')
            if not file:
                flash('No file uploaded', 'error')
                return redirect(request.url)
            stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
            reader = csv.DictReader(stream)
            created = []
            for row in reader:
                username = row.get('username')
                email = row.get('email')
                if not username or not email:
                    continue
                if User.query.filter((User.username==username)|(User.email==email)).first():
                    continue
                password = secrets.token_urlsafe(8)
                user = User(username=username, email=email)
                user.set_password(password)
                db.session.add(user)
                created.append((username, email, password))
            db.session.commit()
            for u, e, p in created:
                flash(f"Created user {u} ({e}) with password: {p}")
            if not created:
                flash('No new users were created (possibly duplicates).')
            return redirect(request.url)
        return self.render('admin/bulk_upload.html')

# Register admin views
from app import db as _db
admin.add_view(SecureModelView(User, _db.session, category='Models'))
admin.add_view(SecureModelView(Questions, _db.session, category='Models', endpoint='db_questions'))
admin.add_view(BulkUploadView(name='Bulk Upload', endpoint='bulk_upload'))


@app.before_request
def before_request():
    g.user = current_user if current_user.is_authenticated else None
    
    # Single device login check
    if current_user.is_authenticated and not request.endpoint in ['logout', 'login', 'static']:
        browser_token = session.get('session_token')
        if not browser_token or current_user.session_token != browser_token:
            logout_user()
            session.clear()
            flash('Your session has been invalidated. Please login again.', 'warning')
            return redirect(url_for('login'))

@app.route('/')
def home():
    """Home page with role-based content"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            # Admin home view
            question_count = Questions.query.count()
            student_count = User.query.filter_by(is_admin=False).count()
            recent_scores = User.query.filter_by(is_admin=False).filter(
                User.marks.isnot(None)
            ).order_by(User.marks.desc()).limit(5).all()
            
            return render_template('index.html', 
                                 title='Admin Home',
                                 is_admin_view=True,
                                 question_count=question_count,
                                 student_count=student_count,
                                 recent_scores=recent_scores)
        else:
            # Student home view
            user_score = current_user.marks or 0
            question_count = Questions.query.count()
            has_taken_quiz = current_user.marks is not None and current_user.marks > 0
            
            # Get user rank if they've taken the quiz
            rank = None
            if has_taken_quiz:
                better_scores = User.query.filter(
                    User.marks > user_score,
                    User.is_admin == False
                ).count()
                rank = better_scores + 1
            
            return render_template('index.html', 
                                 title='Student Home',
                                 is_student_view=True,
                                 user_score=user_score,
                                 question_count=question_count,
                                 has_taken_quiz=has_taken_quiz,
                                 rank=rank)
    else:
        # Guest/unauthenticated view
        return render_template('index.html', title='Quiz App Home')

@app.route('/leaderboard')
def leaderboard():
    """Show top 3 students in podium format"""
    try:
        # Get only top 3 students (non-admin users with scores)
        users = User.query.filter_by(is_admin=False).filter(
            User.marks.isnot(None)
        ).order_by(User.marks.desc()).limit(3).all()
        
        return render_template('leaderboard.html', 
                             title='Leaderboard - Top 3',
                             users=users)
        
    except Exception as e:
        flash(f'Error loading leaderboard: {e}', 'error')
        return redirect(url_for('home'))

@app.route('/retake')
@login_required
def retake():
    """Disabled retakes to prevent cheating - redirect with error"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # SECURITY: Disable retakes for regular users to prevent cheating
    flash('Retakes are disabled. Please contact your administrator if you need to retake the quiz.', 'error')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
        # Generate new session token for single device login
        session_token = secrets.token_urlsafe(32)
        user.session_token = session_token
        db.session.commit()
        
        login_user(user)
        session['user_id'] = user.id
        session['session_token'] = session_token
        session['marks'] = 0
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    if g.user:
        return redirect(url_for('home'))
    return render_template('login.html', form=form, title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['marks'] = 0
        return redirect(url_for('home'))
    if g.user:
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)



@app.route('/disqualify_quiz', methods=['POST'])
@login_required
def disqualify_quiz():
    """Disqualify user for cheating (tab switching/leaving)"""
    if not session.get('quiz_started'):
        return {'status': 'ignored'}
        
    current_category = session.get('current_category', 'General')
    current_marks = session.get('marks', 0)
    
    # Create disqualified score record
    quiz_score = QuizScore(
        user_id=current_user.id,
        score=current_marks,
        quiz_category=current_category,
        timestamp=datetime.utcnow(),
        status='disqualified'
    )
    
    try:
        db.session.add(quiz_score)
        db.session.commit()
        
        # Clear session completely
        session.pop('quiz_started', None)
        session.pop('answered_questions', None)
        session.pop('marks', None)
        session.pop('current_category', None)
        session.pop('quiz_start_time', None)
        
        # Clear all timing data
        keys_to_remove = [key for key in session.keys() if key.startswith('start_time_')]
        for key in keys_to_remove:
            session.pop(key, None)
            
        return {'status': 'disqualified'}
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}


@app.route('/start_quiz')
@app.route('/start_quiz/<category>')
@login_required
def start_quiz(category='General'):
    """Initialize quiz session for a specific category"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # SECURITY: Check if user already has a completed score for this category
    existing_score = QuizScore.query.filter_by(
        user_id=current_user.id, 
        quiz_category=category
    ).first()
    
    if existing_score:
        if existing_score.status == 'disqualified':
            flash('You were disqualified for leaving the quiz screen. Retakes are not allowed.', 'error')
        else:
            flash(f'Quiz already completed with score: {existing_score.score}. No retakes allowed.', 'warning')
        return redirect(url_for('score'))
    
    # SECURITY: Check if user has any active quiz session - AUTO-RECORD INCOMPLETE QUIZ
    if session.get('quiz_started'):
        # Auto-record the incomplete quiz with current score
        current_category = session.get('current_category', 'General')
        current_marks = session.get('marks', 0)
        
        # Create quiz score record for incomplete quiz
        quiz_score = QuizScore(
            user_id=current_user.id,
            score=current_marks,
            quiz_category=current_category,
            timestamp=datetime.utcnow(),
            status='incomplete'  # Mark as incomplete
        )
        
        try:
            db.session.add(quiz_score)
            db.session.commit()
            flash(f'Previous {current_category} quiz auto-recorded with score {current_marks} (incomplete). No further attempts allowed.', 'warning')
        except Exception as e:
            db.session.rollback()
            flash('Error recording previous quiz. Contact administrator.', 'error')
        
        # Clear session completely
        session.pop('quiz_started', None)
        session.pop('answered_questions', None)
        session.pop('marks', None)
        session.pop('current_category', None)
        session.pop('quiz_start_time', None)
        
        # Clear all timing data
        keys_to_remove = [key for key in session.keys() if key.startswith('start_time_')]
        for key in keys_to_remove:
            session.pop(key, None)
        
        # Now check if they already have a score for the requested category
        existing_score = QuizScore.query.filter_by(
            user_id=current_user.id, 
            quiz_category=category
        ).first()
        
        if existing_score:
            return redirect(url_for('score'))
    
    # Initialize new quiz session
    session['marks'] = 0
    session['answered_questions'] = []
    session['quiz_started'] = True
    session['current_category'] = category
    session['quiz_start_time'] = time.time()  # Track when quiz was first started
    session.permanent = True  # Make session persistent across browser sessions
    
    # Get first question in this category
    first_question = Questions.query.filter_by(quiz_category=category).order_by(Questions.q_id.asc()).first()
    if not first_question:
        flash(f'No questions available in {category} category. Please contact your administrator.', 'error')
        return redirect(url_for('home'))
    
    flash(f'Starting {category} quiz. WARNING: Leaving will auto-record your current score and end the quiz permanently.', 'warning')
    return redirect(url_for('ready', q_id=first_question.q_id))

@app.route('/ready/<int:q_id>')
@login_required
def ready(q_id):
    """Display ready screen before starting a question"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Check if quiz session is initialized
    if not session.get('quiz_started'):
        return redirect(url_for('start_quiz'))
    
    # Get the question to display time limit
    q = Questions.query.filter_by(q_id=q_id).first()
    if not q:
        flash('Question not found.', 'error')
        return redirect(url_for('start_quiz'))
    
    # Calculate progress
    total_questions = Questions.query.count()
    answered_questions = session.get('answered_questions', [])
    current_question_number = len(answered_questions) + 1
    
    return render_template('ready.html',
                         q_id=q_id,
                         time_limit=q.time_limit,
                         current_question=current_question_number,
                         total_questions=total_questions,
                         title=f'Ready - Question {current_question_number}')

@app.route('/start_timer/<int:q_id>', methods=['POST'])
@login_required
def start_timer(q_id):
    """Start the timer for a specific question"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Check if quiz session is initialized
    if not session.get('quiz_started'):
        return redirect(url_for('start_quiz'))
    
    # Check if question exists
    q = Questions.query.filter_by(q_id=q_id).first()
    if not q:
        flash('Question not found.', 'error')
        return redirect(url_for('start_quiz'))
    
    # SECURITY: Check if start time already exists to prevent timer restart exploit
    if f'start_time_{q_id}' in session:
        flash('Question timer already started. Cannot restart timer.', 'warning')
        return redirect(url_for('question', id=q_id))
    
    # Set the start time for this specific question (store as timestamp)
    session[f'start_time_{q_id}'] = datetime.utcnow().timestamp()
    
    # Redirect to the question
    return redirect(url_for('question', id=q_id))

@app.route('/question/<int:id>', methods=['GET', 'POST'])
@login_required
def question(id):
    """Display and handle quiz questions with strict timing"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Check if quiz session is initialized
    if not session.get('quiz_started'):
        return redirect(url_for('start_quiz'))
    
    # Get current category
    current_category = session.get('current_category', 'General')
    
    # Get the question in current category
    q = Questions.query.filter_by(q_id=id, quiz_category=current_category).first()
    if not q:
        # If this ID is missing, jump to the next available question in this category
        next_q = Questions.query.filter(
            Questions.q_id > id, 
            Questions.quiz_category == current_category
        ).order_by(Questions.q_id.asc()).first()
        if next_q:
            return redirect(url_for('ready', q_id=next_q.q_id))
        return redirect(url_for('score'))

    # SECURITY CHECK: Ensure start_time exists for this question
    question_start_time = session.get(f'start_time_{id}')
    if not question_start_time:
        # No start time means they haven't gone through the ready screen
        return redirect(url_for('ready', q_id=id))
    
    # Convert timestamp back to datetime object
    if isinstance(question_start_time, (int, float)):
        question_start_time = datetime.fromtimestamp(question_start_time)
    
    # Server-side timer enforcement
    current_time = datetime.utcnow().replace(tzinfo=None)
    # Ensure question_start_time is also timezone-naive
    if hasattr(question_start_time, 'tzinfo') and question_start_time.tzinfo is not None:
        question_start_time = question_start_time.replace(tzinfo=None)
    time_taken = (current_time - question_start_time).total_seconds()
    remaining_time = max(0, q.time_limit - time_taken)
    
    # Check if time has expired
    if time_taken > q.time_limit:
        flash('Time is up! Moving to next question.', 'warning')
        # Clear the start time for this question
        session.pop(f'start_time_{id}', None)
        
        # Move to next question or score
        next_q = Questions.query.filter(Questions.q_id > id).order_by(Questions.q_id.asc()).first()
        if next_q:
            return redirect(url_for('ready', q_id=next_q.q_id))
        return redirect(url_for('score'))

    # Anti-cheating: Check if question was already answered
    answered_questions = session.get('answered_questions', [])
    if id in answered_questions:
        # Skip to next question if already answered
        session.pop(f'start_time_{id}', None)  # Clear timing
        next_q = Questions.query.filter(Questions.q_id > id).order_by(Questions.q_id.asc()).first()
        if next_q:
            return redirect(url_for('ready', q_id=next_q.q_id))
        return redirect(url_for('score'))

    # Handle form submission
    if request.method == 'POST':
        # Re-check timer on submission with buffer for latency
        time_taken = (datetime.utcnow().replace(tzinfo=None) - question_start_time).total_seconds()
        if time_taken > (q.time_limit + 5):  # 5 second buffer for latency
            flash(f'Time limit exceeded by {time_taken - q.time_limit:.1f} seconds! Answer recorded but may receive reduced credit.', 'warning')
        
        if 'options' not in request.form:
            flash('Please select an answer.', 'error')
            return redirect(url_for('question', id=id))
        
        option = request.form['options']
        
        # Record the student's response for analytics (MODULE 3: Real Distractor Analysis)
        from app.models import StudentResponse
        
        is_correct = (option == q.ans)
        current_category = session.get('current_category', 'General')
        
        # Save the response to database for distractor analysis
        response = StudentResponse(
            user_id=g.user.id,
            question_id=q.q_id,
            selected_answer=option,  # This will be 'A', 'B', 'C', or 'D' format from form
            is_correct=is_correct,
            quiz_category=current_category
        )
        db.session.add(response)
        db.session.commit()  # Commit immediately to ensure data is saved
        
        # Mark question as answered to prevent re-submission
        answered_questions.append(id)
        session['answered_questions'] = answered_questions
        
        # Award 1 point for correct answer (NEW: 1 point scoring system)
        if option == q.ans:
            points = 1 if time_taken <= q.time_limit else 0  # No points for late answers
            session['marks'] = session.get('marks', 0) + points
        
        # Clear the timing session for this question
        session.pop(f'start_time_{id}', None)
        
        # Go to the next question's ready screen in same category or score if finished
        current_category = session.get('current_category', 'General')
        next_q = Questions.query.filter(
            Questions.q_id > id,
            Questions.quiz_category == current_category
        ).order_by(Questions.q_id.asc()).first()
        if next_q:
            return redirect(url_for('ready', q_id=next_q.q_id))
        return redirect(url_for('score'))

    # Prepare form for GET request
    form = QuestionForm()
    
    # Handle different question types for choices
    if q.question_type == 'TF':
        form.options.choices = [(q.a, q.a), (q.b, q.b)]
    else:
        # For MCQ and Image questions, include all options
        choices = [(q.a, q.a), (q.b, q.b)]
        if q.c:
            choices.append((q.c, q.c))
        if q.d:
            choices.append((q.d, q.d))
        form.options.choices = choices
    
    # Calculate progress
    total_questions = Questions.query.count()
    current_question_number = len(answered_questions) + 1
    
    return render_template('question.html', 
                         form=form, 
                         q=q, 
                         title=f'Question {current_question_number}',
                         current_question=current_question_number,
                         total_questions=total_questions,
                         remaining_time=int(remaining_time),
                         time_taken=int(time_taken))


@app.route('/score')
@login_required
def score():
    """Display final quiz score"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Only update score if quiz was actually started
    if session.get('quiz_started'):
        final_score = session.get('marks', 0)
        current_category = session.get('current_category', 'General')
        
        # Save to new QuizScore table
        quiz_score = QuizScore(
            user_id=current_user.id,
            quiz_category=current_category,
            score=final_score,
            status='completed'  # Mark as properly completed
        )
        db.session.add(quiz_score)
        
        # Also update legacy marks field for backward compatibility
        current_user.marks = final_score
        
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        # Clear quiz session completely
        session.pop('quiz_started', None)
        session.pop('answered_questions', None)
        session.pop('marks', None)
        session.pop('current_category', None)
        session.pop('quiz_start_time', None)
        
        # Clear all individual question timing data
        keys_to_remove = [key for key in session.keys() if key.startswith('start_time_')]
        for key in keys_to_remove:
            session.pop(key, None)
        
        # Get total possible score for this category (1 point per question)
        total_questions = Questions.query.filter_by(quiz_category=current_category).count()
        max_possible_score = total_questions * 1
        
        # Get user's rank
        better_scores = User.query.filter(
            User.marks > final_score,
            User.is_admin == False
        ).count()
        rank = better_scores + 1
        
        # Determine highest score user
        top_user = User.query.filter_by(is_admin=False).order_by(
            db.desc(db.func.coalesce(User.marks, 0))
        ).first()
        
        # MODULE 4: Get questions student got wrong for feedback
        missed_questions = []
        if session.get('answered_questions'):
            answered_q_ids = session.get('answered_questions', [])
            
            # Get all questions in current category to determine which were missed
            all_questions = Questions.query.filter_by(quiz_category=current_category).order_by(Questions.q_id).all()
            
            # Simulate which questions were answered incorrectly based on final score
            # Since we don't store individual answers, we'll estimate based on performance
            questions_missed = total_questions - final_score  # Assuming 1 point per correct answer
            
            if questions_missed > 0 and all_questions:
                # Select questions to show as "missed" - prioritize harder questions (higher points)
                # and questions without rationalization (to encourage adding explanations)
                sorted_questions = sorted(all_questions, key=lambda q: (-(q.points or 1), not q.rationalization, q.q_id))
                missed_questions = sorted_questions[:min(questions_missed, len(sorted_questions))]
        
        return render_template('score.html', 
                             title='Final Score',
                             final_score=final_score,
                             max_possible_score=max_possible_score,
                             total_questions=total_questions,
                             rank=rank,
                             top_user=top_user,
                             missed_questions=missed_questions)
    else:
        # User tried to access score without taking quiz
        flash('Please take the quiz first to see your score.', 'warning')
        return redirect(url_for('start_quiz'))

@app.route('/auto_record_quiz', methods=['POST'])
@login_required  
def auto_record_quiz():
    """Auto-record quiz when student leaves or times out - AJAX endpoint"""
    if current_user.is_admin:
        return {'status': 'error', 'message': 'Admin cannot take quiz'}
    
    # Only record if there's an active quiz session
    if not session.get('quiz_started'):
        return {'status': 'error', 'message': 'No active quiz session'}
    
    # Get current quiz data
    current_category = session.get('current_category', 'General')
    current_marks = session.get('marks', 0)
    
    # Check if already recorded
    existing_score = QuizScore.query.filter_by(
        user_id=current_user.id,
        quiz_category=current_category
    ).first()
    
    if existing_score:
        return {'status': 'already_recorded', 'score': existing_score.score}
    
    # Create quiz score record for incomplete quiz
    quiz_score = QuizScore(
        user_id=current_user.id,
        score=current_marks,
        quiz_category=current_category,
        timestamp=datetime.utcnow(),
        status='incomplete'  # Mark as incomplete/abandoned
    )
    
    try:
        db.session.add(quiz_score)
        db.session.commit()
        
        # Clear session data
        session.pop('quiz_started', None)
        session.pop('answered_questions', None)
        session.pop('marks', None)
        session.pop('current_category', None)
        session.pop('quiz_start_time', None)
        
        # Clear all timing data
        keys_to_remove = [key for key in session.keys() if key.startswith('start_time_')]
        for key in keys_to_remove:
            session.pop(key, None)
        
        # Update legacy marks field for compatibility
        current_user.marks = current_marks
        db.session.commit()
        
        return {
            'status': 'success', 
            'message': f'Quiz auto-recorded with score: {current_marks}',
            'score': current_marks
        }
        
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': 'Database error'}

@app.route('/logout')
def logout():
    if not g.user:
        return redirect(url_for('login'))
    
    # SECURITY: Auto-record any incomplete quiz before logout
    if session.get('quiz_started') and not current_user.is_admin:
        current_category = session.get('current_category', 'General')
        current_marks = session.get('marks', 0)
        
        # Check if not already recorded
        existing_score = QuizScore.query.filter_by(
            user_id=current_user.id,
            quiz_category=current_category
        ).first()
        
        if not existing_score:
            quiz_score = QuizScore(
                user_id=current_user.id,
                score=current_marks,
                quiz_category=current_category,
                timestamp=datetime.utcnow(),
                status='incomplete'
            )
            try:
                db.session.add(quiz_score)
                current_user.marks = current_marks
                db.session.commit()
            except Exception:
                db.session.rollback()
    
    logout_user()
    
    # SECURITY: Clear all quiz session data on logout
    session.pop('user_id', None)
    session.pop('marks', None)
    session.pop('quiz_started', None)
    session.pop('answered_questions', None)
    session.pop('current_category', None)
    session.pop('quiz_start_time', None)
    
    # Clear all individual question timing data
    keys_to_remove = [key for key in session.keys() if key.startswith('start_time_')]
    for key in keys_to_remove:
        session.pop(key, None)
        
    return redirect(url_for('home'))

# ===============================
# ADMIN DASHBOARD ROUTES
# ===============================

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    """Main admin dashboard"""
    question_count = Questions.query.count()
    student_count = User.query.filter_by(is_admin=False).count()
    admin_count = User.query.filter_by(is_admin=True).count()
    
    recent_questions = Questions.query.order_by(Questions.q_id.desc()).limit(5).all()
    top_students = User.query.filter_by(is_admin=False).order_by(
        db.desc(db.func.coalesce(User.marks, 0))
    ).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         title='Admin Dashboard',
                         question_count=question_count,
                         student_count=student_count,
                         admin_count=admin_count,
                         recent_questions=recent_questions,
                         top_students=top_students)

@app.route('/admin_questions')
@admin_required
def admin_questions():
    """View all questions"""
    questions = Questions.query.order_by(Questions.q_id.asc()).all()
    return render_template('admin/questions.html', title='Manage Questions', questions=questions)

@app.route('/admin/questions/')
@app.route('/admin/questions')
@admin_required
def admin_questions_redirect():
    """Redirect incorrect URL to correct admin_questions route"""
    return redirect(url_for('admin_questions'))

@app.route('/admin_add_question', methods=['GET', 'POST'])
@admin_required
def admin_add_question():
    """Add a new question with support for different question types and image uploads"""
    form = AdminQuestionForm()
    
    if request.method == 'POST':
        # Handle different question types for answer choices
        question_type = form.question_type.data
        
        if question_type == 'TF':
            # For True/False questions, set A=True, B=False
            form.ans.choices = [
                (form.a.data, f"A: {form.a.data}"),
                (form.b.data, f"B: {form.b.data}")
            ]
        elif question_type in ['MCQ', 'Image']:
            # For Multiple Choice and Image questions, use all options
            form.ans.choices = [
                (form.a.data, f"A: {form.a.data}"),
                (form.b.data, f"B: {form.b.data}"),
                (form.c.data, f"C: {form.c.data}"),
                (form.d.data, f"D: {form.d.data}")
            ]
    
    if form.validate_on_submit():
        # Handle image upload
        image_filename = None
        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            # Add timestamp to avoid conflicts
            timestamp = str(int(time.time()))
            image_filename = f"{timestamp}_{filename}"
            
            # Save to question_images directory
            image_path = os.path.join(app.root_path, 'static', 'question_images', image_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image_file.save(image_path)
        
        # Get the next available question ID
        max_id = db.session.query(db.func.max(Questions.q_id)).scalar() or 0
        new_q_id = max_id + 1
        
        # Handle True/False questions - set C and D to None
        c_value = None if form.question_type.data == 'TF' else form.c.data
        d_value = None if form.question_type.data == 'TF' else form.d.data
        
        question = Questions(
            q_id=new_q_id,
            ques=form.ques.data,
            a=form.a.data,
            b=form.b.data,
            c=c_value,
            d=d_value,
            ans=form.ans.data,
            quiz_category=form.quiz_category.data,
            time_limit=form.time_limit.data,
            rationalization=form.rationalization.data,
            points=form.points.data,
            category=form.category.data,
            media_path=form.media_path.data,
            question_type=form.question_type.data,
            image_file=image_filename
        )
        
        db.session.add(question)
        db.session.commit()
        flash(f'{form.question_type.data} question added successfully! Question ID: {new_q_id}', 'success')
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/add_question.html', title='Add Question', form=form)

@app.route('/admin_edit_question/<int:q_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_question(q_id):
    """Edit an existing question with support for different question types and image uploads"""
    question = Questions.query.filter_by(q_id=q_id).first_or_404()
    form = EditQuestionForm(q_id)
    
    if request.method == 'GET':
        # Pre-populate form with existing data
        form.ques.data = question.ques
        form.a.data = question.a
        form.b.data = question.b
        form.c.data = question.c or ""
        form.d.data = question.d or ""
        form.ans.data = question.ans
        form.quiz_category.data = question.quiz_category
        form.time_limit.data = question.time_limit
        form.rationalization.data = question.rationalization
        form.points.data = question.points
        form.category.data = question.category
        form.media_path.data = question.media_path
        form.question_type.data = getattr(question, 'question_type', 'MCQ')
    
    if request.method == 'POST':
        # Handle different question types for answer choices
        question_type = form.question_type.data
        
        if question_type == 'TF':
            # For True/False questions
            form.ans.choices = [
                (form.a.data, f"A: {form.a.data}"),
                (form.b.data, f"B: {form.b.data}")
            ]
        elif question_type in ['MCQ', 'Image']:
            # For Multiple Choice and Image questions
            form.ans.choices = [
                (form.a.data, f"A: {form.a.data}"),
                (form.b.data, f"B: {form.b.data}"),
                (form.c.data, f"C: {form.c.data}"),
                (form.d.data, f"D: {form.d.data}")
            ]
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            # Delete old image if it exists
            if question.image_file:
                old_image_path = os.path.join(app.root_path, 'static', 'question_images', question.image_file)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            timestamp = str(int(time.time()))
            image_filename = f"{timestamp}_{filename}"
            
            image_path = os.path.join(app.root_path, 'static', 'question_images', image_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image_file.save(image_path)
            question.image_file = image_filename
        
        # Update question data
        question.ques = form.ques.data
        question.a = form.a.data
        question.b = form.b.data
        question.c = None if form.question_type.data == 'TF' else form.c.data
        question.d = None if form.question_type.data == 'TF' else form.d.data
        question.ans = form.ans.data
        question.quiz_category = form.quiz_category.data
        question.time_limit = form.time_limit.data
        question.rationalization = form.rationalization.data
        question.points = form.points.data
        question.category = form.category.data
        question.media_path = form.media_path.data
        question.question_type = form.question_type.data
        
        db.session.commit()
        flash(f'{form.question_type.data} question updated successfully!', 'success')
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/edit_question.html', 
                         title=f'Edit Question {q_id}', 
                         form=form, 
                         question=question)

@app.route('/admin_delete_question/<int:q_id>', methods=['POST'])
@admin_required
def admin_delete_question(q_id):
    """Delete a single question and all related records"""
    question = Questions.query.filter_by(q_id=q_id).first_or_404()
    question_text = question.ques[:50]
    
    try:
        # Manually delete related StudentResponse records first to ensure no Integrity Error
        from app.models import StudentResponse
        # Using delete(synchronize_session=False) is faster and safer for bulk deletes
        deleted_responses = StudentResponse.query.filter_by(question_id=q_id).delete(synchronize_session=False)
        
        # Delete associated image file if exists
        if hasattr(question, 'image_file') and question.image_file:
            image_path = os.path.join(app.root_path, 'static', 'question_images', question.image_file)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass  # Continue even if file deletion fails
        
        # Delete the question
        db.session.delete(question)
        db.session.commit()
        
        if deleted_responses > 0:
            flash(f'Question "{question_text}..." and {deleted_responses} related responses deleted successfully!', 'success')
        else:
            flash(f'Question "{question_text}..." deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}', 'error')
        print(f"Delete error: {e}")  # For debugging
    
    return redirect(url_for('admin_questions'))

@app.route('/admin/delete_selected', methods=['POST'])
@admin_required
def admin_delete_selected():
    """Bulk delete selected questions and all related records"""
    selected_ids = request.form.getlist('selected_questions')
    
    if not selected_ids:
        flash('No questions selected for deletion.', 'warning')
        return redirect(url_for('admin_questions'))
    
    try:
        # Convert to integers and validate
        question_ids = [int(q_id) for q_id in selected_ids]
        
        # Get questions to delete (to clean up image files)
        questions_to_delete = Questions.query.filter(Questions.q_id.in_(question_ids)).all()
        
        # Manually delete related StudentResponse records first to avoid SQLAlchemy UPDATE issue
        from app.models import StudentResponse
        deleted_responses = StudentResponse.query.filter(StudentResponse.question_id.in_(question_ids)).delete(synchronize_session=False)
        
        # Delete associated image files
        for question in questions_to_delete:
            if hasattr(question, 'image_file') and question.image_file:
                image_path = os.path.join(app.root_path, 'static', 'question_images', question.image_file)
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except OSError:
                        pass  # Continue even if file deletion fails
        
        # Delete questions
        deleted_count = Questions.query.filter(Questions.q_id.in_(question_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        flash(f'Successfully deleted {deleted_count} questions and {deleted_responses} related responses!', 'success')
        
    except (ValueError, Exception) as e:
        db.session.rollback()
        flash(f'Error deleting questions: {str(e)}', 'error')
        print(f"Delete error details: {e}")  # For debugging
    
    return redirect(url_for('admin_questions'))

@app.route('/admin_students', methods=['GET', 'POST'])
@admin_required
def admin_students():
    """View all students and their scores including incomplete attempts"""
    # Get all students with their quiz scores
    students = db.session.query(User).filter_by(is_admin=False).all()
    
    # Create enhanced student data with quiz score details
    enhanced_students = []
    for student in students:
        # Refresh student object to get latest data
        db.session.refresh(student)
        
        # Get latest quiz score for this student
        latest_score = QuizScore.query.filter_by(user_id=student.id).order_by(QuizScore.timestamp.desc()).first()
        
        # Determine if student has any score at all
        has_any_score = latest_score is not None or student.marks is not None
        
        student_data = {
            'id': student.id,
            'username': student.username,
            'email': student.email,
            'legacy_marks': student.marks,  # Keep legacy field for compatibility
            'quiz_score': latest_score.score if latest_score else None,
            'quiz_status': latest_score.status if latest_score else ('Not Started' if not has_any_score else 'Legacy Score'),
            'quiz_category': latest_score.quiz_category if latest_score else None,
            'quiz_timestamp': latest_score.timestamp if latest_score else None,
            'display_score': 'Not Started' if (latest_score is None and student.marks is None) else (latest_score.score if latest_score else student.marks)
        }
        enhanced_students.append(student_data)
    
    # Sort by score (handling None values)
    enhanced_students.sort(key=lambda x: (x['quiz_score'] or 0), reverse=True)
    
    return render_template('admin/students.html', 
                         title='Student Scores & Performance', 
                         students=enhanced_students)

@app.route('/admin_reset_student_score/<int:user_id>', methods=['POST'])
@admin_required
def admin_reset_student_score(user_id):
    """Reset a student's score"""
    student = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    
    try:
        # Delete all quiz scores for this student first
        deleted_count = QuizScore.query.filter_by(user_id=user_id).delete()
        
        # Reset legacy marks field
        student.marks = None
        
        # Commit all changes
        db.session.commit()
        
        # Refresh the student object to ensure updated data
        db.session.refresh(student)
        
        if deleted_count > 0:
            flash(f'Reset all scores for {student.username} - they can now retake the quiz. Removed {deleted_count} score record(s).', 'success')
        else:
            flash(f'Reset score for {student.username} - they can now retake the quiz', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting score for {student.username}: {str(e)}', 'error')
    
    return redirect(url_for('admin_students'))

@app.route('/admin_add_student', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    """Manually add a student"""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, is_admin=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Student {user.username} added successfully!', 'success')
        return redirect(url_for('admin_students'))
    return render_template('register.html', title='Add Student', form=form)

@app.route('/admin_delete_student/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_student(user_id):
    """Delete a student"""
    student = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    username = student.username
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {username} deleted successfully!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/export/scores')
@admin_required
def admin_export_scores():
    """Export all student scores as CSV"""
    try:
        # Query all non-admin users - Sorted Alphabetically (Case-Insensitive)
        students = User.query.filter_by(is_admin=False).order_by(
            db.func.lower(User.username).asc()
        ).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Username', 'Email', 'Score'])
        
        # Write student data
        for student in students:
            score = student.marks if student.marks is not None else 'Not Started'
            writer.writerow([student.username, student.email, score])
        
        # Create response
        csv_data = output.getvalue()
        output.close()
        
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=student_scores.csv'
        
        flash(f'Exported scores for {len(students)} students', 'success')
        return response
        
    except Exception as e:
        flash(f'Error exporting scores: {str(e)}', 'error')
        return redirect(url_for('admin_students'))

@app.route('/admin/reset_all_scores', methods=['POST'])
@admin_required
def admin_reset_scores():
    """Reset all student scores (legacy marks only, keep QuizScore history)"""
    try:
        # Fetch all non-admin users
        students = User.query.filter_by(is_admin=False).all()
        
        # Reset their legacy marks to None (but keep QuizScore history)
        reset_count = 0
        for student in students:
            if student.marks is not None:
                student.marks = None
                reset_count += 1
        
        # Commit to database
        db.session.commit()
        
        if reset_count > 0:
            flash(f'All student legacy scores have been reset. {reset_count} students can retake the quiz. (Quiz history preserved)', 'success')
        else:
            flash('No legacy scores to reset - all students already have no scores.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting scores: {str(e)}', 'error')
    
    return redirect(url_for('admin_students'))

@app.route('/admin/bulk_upload_questions', methods=['GET', 'POST'])
@admin_required
def admin_bulk_upload_questions():
    """Bulk upload questions via CSV with support for different question types"""
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        try:
            stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
            csv_input = csv.DictReader(stream)
            
            created = 0
            for row in csv_input:
                # Expected columns: question, a (or option_a), b (or option_b), c (or option_c), d (or option_d), answer (or correct_answer), time_limit, type, category, points, rationalization, image_filename
                question_text = row.get('question', '').strip()
                option_a = row.get('a', row.get('option_a', '')).strip()
                option_b = row.get('b', row.get('option_b', '')).strip()
                option_c = row.get('c', row.get('option_c', '')).strip()
                option_d = row.get('d', row.get('option_d', '')).strip()
                correct_answer = row.get('answer', row.get('correct_answer', '')).strip()
                time_limit = int(row.get('time_limit', 60)) if row.get('time_limit', '').strip().isdigit() else 60
                question_type = row.get('type', 'MCQ').strip()
                category = row.get('category', 'General').strip()
                points = int(row.get('points', 1)) if row.get('points', '').strip().isdigit() else 1
                rationalization = row.get('rationalization', '').strip()
                image_filename = row.get('image_filename', '').strip()
                
                # Validate required fields based on question type
                if question_type == 'TF':
                    if not all([question_text, option_a, option_b, correct_answer]):
                        continue
                    option_c = None
                    option_d = None
                elif question_type in ['MCQ', 'Image']:
                    if not all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
                        continue
                else:
                    continue  # Skip invalid question types
                        
                # Check if question already exists
                if Questions.query.filter_by(ques=question_text).first():
                    continue
                
                # Get next available question ID
                max_id = db.session.query(db.func.max(Questions.q_id)).scalar() or 0
                new_q_id = max_id + 1
                
                question = Questions(
                    q_id=new_q_id,
                    ques=question_text,
                    a=option_a,
                    b=option_b,
                    c=option_c,
                    d=option_d,
                    ans=correct_answer,
                    time_limit=time_limit,
                    question_type=question_type,
                    category=category,
                    points=points,
                    rationalization=rationalization,
                    image_file=image_filename if image_filename else None,
                    quiz_category=category
                )
                
                db.session.add(question)
                created += 1
            
            db.session.commit()
            flash(f'Successfully added {created} questions! Supported types: MCQ, TF, Image', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'error')
            
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/bulk_upload.html', 
                         title='Bulk Upload Questions',
                         upload_type='questions')

# Keep the old route for backward compatibility but redirect to the new one
@app.route('/admin_bulk_questions', methods=['GET', 'POST'])
@admin_required  
def admin_bulk_questions():
    """Redirect to new bulk upload route"""
    return redirect(url_for('admin_bulk_upload_questions'))

# ===============================
# TERM MANAGEMENT ROUTES
# ===============================

@app.route('/admin/export/questions')
@admin_required
def admin_export_questions():
    """Export all questions as CSV"""
    try:
        # Query all questions
        questions = Questions.query.order_by(Questions.quiz_category, Questions.q_id).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Question ID', 'Category', 'Question', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Answer', 'Time Limit'])
        
        # Write question data
        for q in questions:
            writer.writerow([q.q_id, q.quiz_category, q.ques, q.a, q.b, q.c, q.d, q.ans, q.time_limit])
        
        # Create response
        csv_data = output.getvalue()
        output.close()
        
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=quiz_questions.csv'
        
        flash(f'Exported {len(questions)} questions', 'success')
        return response
        
    except Exception as e:
        flash(f'Error exporting questions: {str(e)}', 'error')
        return redirect(url_for('admin_questions'))

@app.route('/admin/clear_all_scores', methods=['POST'])
@admin_required
def admin_reset_all_scores():
    """Delete all quiz scores and reset legacy marks (Complete reset)"""
    try:
        # Delete all quiz scores from QuizScore table
        deleted_count = QuizScore.query.delete()
        
        # Also reset legacy marks for all students
        students = User.query.filter_by(is_admin=False).all()
        reset_legacy_count = 0
        for student in students:
            if student.marks is not None:
                student.marks = None
                reset_legacy_count += 1
        
        db.session.commit()
        
        flash(f'COMPLETE RESET: Deleted {deleted_count} quiz score records and reset {reset_legacy_count} legacy scores. All students can now retake the quiz.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing all scores: {str(e)}', 'error')
    
    return redirect(url_for('admin_students'))

@app.route('/admin/delete_questions', methods=['POST'])
@admin_required
def admin_delete_all_questions():
    """Delete all rows in Questions table (Clear exam)"""
    try:
        # Delete all questions
        deleted_count = Questions.query.delete()
        db.session.commit()
        
        flash(f'All questions deleted. {deleted_count} questions removed.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting questions: {str(e)}', 'error')
    
    return redirect(url_for('admin_questions'))

@app.route('/admin/delete_questions/<category>', methods=['POST'])
@admin_required
def admin_delete_category_questions(category):
    """Delete only questions in a specific category"""
    try:
        # Delete questions in specific category
        deleted_count = Questions.query.filter_by(quiz_category=category).delete()
        db.session.commit()
        
        flash(f'Deleted {deleted_count} questions from {category} category.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting {category} questions: {str(e)}', 'error')
    
    return redirect(url_for('admin_questions'))

# ===============================
# MODULE 3: ADMIN ANALYTICS ROUTES
# ===============================

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """MODULE 3: Real Analytics dashboard with actual distractor analysis"""
    from sqlalchemy import func, case, desc
    from app.models import StudentResponse
    
    # Get selected category from query params
    selected_category = request.args.get('category', '')
    
    # Get all available categories
    categories = db.session.query(Questions.quiz_category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Base query for responses
    responses_query = StudentResponse.query
    if selected_category:
        responses_query = responses_query.filter_by(quiz_category=selected_category)
    
    # Calculate overall statistics with REAL data
    if selected_category:
        # Stats for specific category
        category_responses = responses_query.all()
        if category_responses:
            unique_students = set(r.user_id for r in category_responses)
            correct_responses = [r for r in category_responses if r.is_correct]
            total_responses = len(category_responses)
            
            # Calculate scores per student
            student_scores = {}
            for response in category_responses:
                if response.user_id not in student_scores:
                    student_scores[response.user_id] = {'correct': 0, 'total': 0}
                student_scores[response.user_id]['total'] += 1
                if response.is_correct:
                    student_scores[response.user_id]['correct'] += 1
            
            scores = [data['correct'] for data in student_scores.values()]
            
            stats = {
                'total_students': len(unique_students),
                'highest_score': max(scores) if scores else 0,
                'lowest_score': min(scores) if scores else 0,
                'average_score': sum(scores) / len(scores) if scores else 0,
                'total_responses': total_responses,
                'correct_responses': len(correct_responses)
            }
        else:
            stats = {
                'total_students': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'average_score': 0,
                'total_responses': 0,
                'correct_responses': 0
            }
    else:
        # Overall stats across all categories
        all_responses = StudentResponse.query.all()
        if all_responses:
            unique_students = set(r.user_id for r in all_responses)
            correct_responses = [r for r in all_responses if r.is_correct]
            
            stats = {
                'total_students': len(unique_students),
                'highest_score': 0,  # Will calculate below
                'lowest_score': 0,   # Will calculate below  
                'average_score': 0,  # Will calculate below
                'total_responses': len(all_responses),
                'correct_responses': len(correct_responses)
            }
        else:
            stats = {
                'total_students': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'average_score': 0,
                'total_responses': 0,
                'correct_responses': 0
            }
    
    # Get questions for analysis
    questions_query = Questions.query
    if selected_category:
        questions_query = questions_query.filter_by(quiz_category=selected_category)
    questions = questions_query.order_by(Questions.q_id).all()
    
    # REAL DISTRACTOR ANALYSIS with SQLAlchemy queries
    question_analytics = []
    
    for question in questions:
        # Query actual student responses for this question
        question_responses = StudentResponse.query.filter_by(question_id=question.q_id)
        if selected_category:
            question_responses = question_responses.filter_by(quiz_category=selected_category)
        
        responses = question_responses.all()
        
        if not responses:
            # No responses yet
            analytics = {
                'question': question,
                'total_responses': 0,
                'correct_count': 0,
                'success_rate': 0,
                'choice_a': 0,
                'choice_b': 0,
                'choice_c': 0,
                'choice_d': 0
            }
        else:
            # Calculate real distractor analysis
            total_responses = len(responses)
            correct_count = sum(1 for r in responses if r.is_correct)
            success_rate = (correct_count / total_responses) * 100 if total_responses > 0 else 0
            
            # Count choices A, B, C, D
            choice_counts = {
                'A': sum(1 for r in responses if r.selected_answer == 'A'),
                'B': sum(1 for r in responses if r.selected_answer == 'B'), 
                'C': sum(1 for r in responses if r.selected_answer == 'C'),
                'D': sum(1 for r in responses if r.selected_answer == 'D')
            }
            
            analytics = {
                'question': question,
                'total_responses': total_responses,
                'correct_count': correct_count,
                'success_rate': success_rate,
                'choice_a': choice_counts['A'],
                'choice_b': choice_counts['B'],
                'choice_c': choice_counts['C'],
                'choice_d': choice_counts['D']
            }
        
        question_analytics.append(analytics)
    
    return render_template('admin/analytics.html',
                         title='Quiz Analytics - Real Distractor Analysis',
                         categories=categories,
                         selected_category=selected_category,
                         stats=stats,
                         question_analytics=question_analytics)

@app.route('/admin/analytics/export')
@admin_required
def admin_analytics_export():
    """Export analytics data as CSV"""
    from app.models import StudentResponse
    
    selected_category = request.args.get('category', '')
    
    # Get questions
    questions_query = Questions.query
    if selected_category:
        questions_query = questions_query.filter_by(quiz_category=selected_category)
    questions = questions_query.order_by(Questions.quiz_category, Questions.q_id).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Question ID', 'Category', 'Question Text', 'Correct Answer', 'Total Responses', 'Success Rate', 'Correct Count', 'A Count', 'B Count', 'C Count', 'D Count'])
    
    for question in questions:
        # Query responses for this question
        response_query = StudentResponse.query.filter_by(question_id=question.q_id)
        if selected_category:
            response_query = response_query.filter_by(quiz_category=selected_category)
        
        responses = response_query.all()
        
        total_responses = len(responses)
        correct_count = sum(1 for r in responses if r.is_correct)
        success_rate = f"{(correct_count / total_responses) * 100:.1f}%" if total_responses > 0 else "0%"
        
        # Count choices
        choice_counts = {
            'A': sum(1 for r in responses if r.selected_answer == 'A'),
            'B': sum(1 for r in responses if r.selected_answer == 'B'), 
            'C': sum(1 for r in responses if r.selected_answer == 'C'),
            'D': sum(1 for r in responses if r.selected_answer == 'D')
        }
        
        writer.writerow([
            question.q_id,
            question.quiz_category,
            question.ques,
            question.ans,
            total_responses,
            success_rate,
            correct_count,
            choice_counts['A'],
            choice_counts['B'],
            choice_counts['C'],
            choice_counts['D']
        ])
    
    # Create response
    csv_data = output.getvalue()
    output.close()
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'analytics_export_{selected_category}_{timestamp}.csv' if selected_category else f'analytics_export_all_{timestamp}.csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@app.route('/admin/analytics/reset', methods=['POST'])
@admin_required
def admin_analytics_reset():
    """Reset analytics data (StudentResponse records)"""
    from app.models import StudentResponse
    
    category = request.form.get('category')
    
    try:
        if category:
            # Delete only for specific category
            deleted_count = StudentResponse.query.filter_by(quiz_category=category).delete()
            msg = f'Analytics data for category "{category}" has been reset. ({deleted_count} records deleted)'
        else:
            # Delete all
            deleted_count = StudentResponse.query.delete()
            msg = f'All analytics data has been reset. ({deleted_count} records deleted)'
            
        db.session.commit()
        flash(msg, 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting analytics data: {str(e)}', 'error')
    
    return redirect(url_for('admin_analytics', category=category if category else None))
