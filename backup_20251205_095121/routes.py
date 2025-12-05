from app import app, db, admin
from flask import render_template, request, redirect, url_for, session, g, flash, make_response
try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlparse as url_parse
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
            stream = io.StringIO(file.stream.read().decode('utf-8'))
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
admin.add_view(SecureModelView(Questions, _db.session, category='Models'))
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
    """Allow student to retake the quiz"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Clear quiz session and restart
    session.pop('quiz_started', None)
    session.pop('answered_questions', None)
    session['marks'] = 0
    
    return redirect(url_for('start_quiz'))

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



def _get_first_and_last_question_ids():
    first = db.session.query(db.func.min(Questions.q_id)).scalar()
    last = db.session.query(db.func.max(Questions.q_id)).scalar()
    return first, last

@app.route('/start_quiz')
@app.route('/start_quiz/<category>')
@login_required
def start_quiz(category='General'):
    """Initialize quiz session for a specific category"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Check if user already has a score for this category
    existing_score = QuizScore.query.filter_by(
        user_id=current_user.id, 
        quiz_category=category
    ).first()
    
    if existing_score:
        flash(f'You have already completed the {category} quiz. Contact admin if you need to retake.', 'info')
        return redirect(url_for('score'))
    
    # Reset quiz session and store category
    session['marks'] = 0
    session['answered_questions'] = []
    session['quiz_started'] = True
    session['current_category'] = category
    session['start_time'] = time.time()
    
    # Get first question in this category
    first_question = Questions.query.filter_by(quiz_category=category).order_by(Questions.q_id.asc()).first()
    if not first_question:
        flash(f'No questions available in {category} category. Please contact your administrator.', 'error')
        return redirect(url_for('home'))
    
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
    form.options.choices = [(q.a, q.a), (q.b, q.b), (q.c, q.c), (q.d, q.d)]
    
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
            score=final_score
        )
        db.session.add(quiz_score)
        
        # Also update legacy marks field for backward compatibility
        current_user.marks = final_score
        
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        # Clear quiz session
        session.pop('quiz_started', None)
        session.pop('answered_questions', None)
        session.pop('marks', None)
        session.pop('current_category', None)
        
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
        
        return render_template('score.html', 
                             title='Final Score',
                             final_score=final_score,
                             max_possible_score=max_possible_score,
                             total_questions=total_questions,
                             rank=rank,
                             top_user=top_user)
    else:
        # User tried to access score without taking quiz
        flash('Please take the quiz first to see your score.', 'warning')
        return redirect(url_for('start_quiz'))

@app.route('/logout')
def logout():
    if not g.user:
        return redirect(url_for('login'))
    logout_user()
    session.pop('user_id', None)
    session.pop('marks', None)
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

@app.route('/admin_add_question', methods=['GET', 'POST'])
@admin_required
def admin_add_question():
    """Add a new question"""
    form = AdminQuestionForm()
    
    if request.method == 'POST':
        # Set the choices dynamically based on form data
        form.ans.choices = [
            (form.a.data, f"A: {form.a.data}"),
            (form.b.data, f"B: {form.b.data}"),
            (form.c.data, f"C: {form.c.data}"),
            (form.d.data, f"D: {form.d.data}")
        ]
    
    if form.validate_on_submit():
        # Get the next available question ID
        max_id = db.session.query(db.func.max(Questions.q_id)).scalar() or 0
        new_q_id = max_id + 1
        
        question = Questions(
            q_id=new_q_id,
            ques=form.ques.data,
            a=form.a.data,
            b=form.b.data,
            c=form.c.data,
            d=form.d.data,
            ans=form.ans.data,
            quiz_category=form.quiz_category.data,
            time_limit=form.time_limit.data
        )
        
        db.session.add(question)
        db.session.commit()
        flash(f'Question added successfully! Question ID: {new_q_id}', 'success')
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/add_question.html', title='Add Question', form=form)

@app.route('/admin_edit_question/<int:q_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_question(q_id):
    """Edit an existing question"""
    question = Questions.query.filter_by(q_id=q_id).first_or_404()
    form = EditQuestionForm(q_id)
    
    if request.method == 'GET':
        # Pre-populate form with existing data
        form.ques.data = question.ques
        form.a.data = question.a
        form.b.data = question.b
        form.c.data = question.c
        form.d.data = question.d
        form.ans.data = question.ans
        form.quiz_category.data = question.quiz_category
        form.time_limit.data = question.time_limit
    
    if request.method == 'POST':
        # Set the choices dynamically based on form data
        form.ans.choices = [
            (form.a.data, f"A: {form.a.data}"),
            (form.b.data, f"B: {form.b.data}"),
            (form.c.data, f"C: {form.c.data}"),
            (form.d.data, f"D: {form.d.data}")
        ]
    
    if form.validate_on_submit():
        question.ques = form.ques.data
        question.a = form.a.data
        question.b = form.b.data
        question.c = form.c.data
        question.d = form.d.data
        question.ans = form.ans.data
        question.quiz_category = form.quiz_category.data
        question.time_limit = form.time_limit.data
        
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/edit_question.html', 
                         title=f'Edit Question {q_id}', 
                         form=form, 
                         question=question)

@app.route('/admin_delete_question/<int:q_id>', methods=['POST'])
@admin_required
def admin_delete_question(q_id):
    """Delete a question"""
    question = Questions.query.filter_by(q_id=q_id).first_or_404()
    db.session.delete(question)
    db.session.commit()
    flash(f'Question "{question.ques[:50]}..." deleted successfully!', 'success')
    return redirect(url_for('admin_questions'))

@app.route('/admin_students')
@admin_required
def admin_students():
    """View all students and their scores"""
    students = User.query.filter_by(is_admin=False).order_by(
        db.desc(db.func.coalesce(User.marks, 0))
    ).all()
    return render_template('admin/students.html', title='Student Scores', students=students)

@app.route('/admin_reset_student_score/<int:user_id>', methods=['POST'])
@admin_required
def admin_reset_student_score(user_id):
    """Reset a student's score"""
    student = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    student.marks = None  # Set to None to allow retakes
    db.session.commit()
    flash(f'Reset score for {student.username} - they can now retake the quiz', 'success')
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
        # Query all non-admin users
        students = User.query.filter_by(is_admin=False).order_by(
            db.desc(db.func.coalesce(User.marks, 0))
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

@app.route('/admin/reset_scores', methods=['POST'])
@admin_required
def admin_reset_scores():
    """Reset all student scores"""
    try:
        # Fetch all non-admin users
        students = User.query.filter_by(is_admin=False).all()
        
        # Reset their marks to None
        reset_count = 0
        for student in students:
            if student.marks is not None:
                student.marks = None
                reset_count += 1
        
        # Commit to database
        db.session.commit()
        
        if reset_count > 0:
            flash(f'All student scores have been reset. {reset_count} students can now retake the quiz.', 'success')
        else:
            flash('No scores to reset - all students already have no scores.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting scores: {str(e)}', 'error')
    
    return redirect(url_for('admin_students'))

@app.route('/admin/bulk_upload_questions', methods=['GET', 'POST'])
@admin_required
def admin_bulk_upload_questions():
    """Bulk upload questions via CSV"""
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        try:
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            csv_input = csv.reader(stream)
            next(csv_input)  # Skip header
            
            created = 0
            for row in csv_input:
                # Expected format: Question, A, B, C, D, Answer, Time
                if len(row) >= 6:
                    question_text = row[0].strip()
                    option_a = row[1].strip()
                    option_b = row[2].strip()
                    option_c = row[3].strip()
                    option_d = row[4].strip()
                    correct_answer = row[5].strip()
                    time_limit = int(row[6]) if len(row) > 6 and row[6].strip().isdigit() else 60
                    
                    if not all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
                        continue
                        
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
                        time_limit=time_limit
                    )
                    
                    db.session.add(question)
                    created += 1
            
            db.session.commit()
            flash(f'Successfully added {created} questions!', 'success')
            
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

@app.route('/admin/reset_scores', methods=['POST'])
@admin_required
def admin_reset_all_scores():
    """Delete all rows in QuizScore table (Clear student history)"""
    try:
        # Delete all quiz scores
        deleted_count = QuizScore.query.delete()
        
        # Also reset legacy marks for backward compatibility
        students = User.query.filter_by(is_admin=False).all()
        for student in students:
            student.marks = None
        
        db.session.commit()
        
        flash(f'All student history cleared. {deleted_count} score records deleted.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing scores: {str(e)}', 'error')
    
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