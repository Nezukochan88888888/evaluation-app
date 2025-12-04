from app import app, db, admin
from flask import render_template, request, redirect, url_for, session, g, flash
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, QuestionForm, AdminQuestionForm, EditQuestionForm
from app.models import User, Questions
from sqlalchemy import desc
from flask_login import current_user, login_user, logout_user, login_required
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
from functools import wraps
import csv
import io
import secrets


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
    try:
        # Simple approach - just get all users
        users = User.query.all()
        # Sort in Python instead of SQL to avoid database issues
        users = sorted(users, key=lambda x: x.marks or 0, reverse=True)[:10]
        
        # Create simple HTML response to avoid template issues
        html = f"""
        <html>
        <head><title>Leaderboard</title></head>
        <body style="font-family: Arial; padding: 20px;">
        <h1>Leaderboard</h1>
        <ol>
        """
        
        for user in users:
            html += f"<li>{user.username} — {user.marks or 0} points</li>"
        
        html += """
        </ol>
        <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<html><body><h1>Leaderboard Error</h1><p>Error: {e}</p><a href='/'>Back to Home</a></body></html>", 500

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
            return redirect(url_for('login'))
        login_user(user)
        session['user_id'] = user.id
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
@login_required
def start_quiz():
    """Initialize quiz session"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Reset quiz session
    session['marks'] = 0
    session['answered_questions'] = []
    session['quiz_started'] = True
    
    first = db.session.query(db.func.min(Questions.q_id)).scalar()
    if first is None:
        flash('No questions available. Please contact your administrator.', 'error')
        return redirect(url_for('home'))
    
    return redirect(url_for('question', id=first))

@app.route('/question/<int:id>', methods=['GET', 'POST'])
@login_required
def question(id):
    """Display and handle quiz questions"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Check if quiz session is initialized
    if not session.get('quiz_started'):
        return redirect(url_for('start_quiz'))
    
    form = QuestionForm()
    first_id, last_id = _get_first_and_last_question_ids()
    if first_id is None or last_id is None:
        # No questions available
        flash('No questions available. Please contact your administrator.', 'error')
        return redirect(url_for('home'))

    # End-of-quiz handling: if id exceeds last question id, go to score
    if id > last_id:
        return redirect(url_for('score'))

    q = Questions.query.filter_by(q_id=id).first()
    if not q:
        # If this ID is missing, jump to the next available question id
        next_q = Questions.query.filter(Questions.q_id > id).order_by(Questions.q_id.asc()).first()
        if next_q:
            return redirect(url_for('question', id=next_q.q_id))
        return redirect(url_for('score'))

    # Anti-cheating: Check if question was already answered
    answered_questions = session.get('answered_questions', [])
    if id in answered_questions:
        # Skip to next question if already answered
        next_q = Questions.query.filter(Questions.q_id > id).order_by(Questions.q_id.asc()).first()
        if next_q:
            return redirect(url_for('question', id=next_q.q_id))
        return redirect(url_for('score'))

    if request.method == 'POST':
        if 'options' not in request.form:
            flash('Please select an answer.', 'error')
            return redirect(url_for('question', id=id))
            
        option = request.form['options']
        
        # Mark question as answered to prevent re-submission
        answered_questions.append(id)
        session['answered_questions'] = answered_questions
        
        # Award points for correct answer
        if option == q.ans:
            session['marks'] = session.get('marks', 0) + 10
        
        # Go to the next available question id or score if finished
        next_q = Questions.query.filter(Questions.q_id > id).order_by(Questions.q_id.asc()).first()
        if next_q:
            return redirect(url_for('question', id=next_q.q_id))
        return redirect(url_for('score'))

    form.options.choices = [(q.a, q.a), (q.b, q.b), (q.c, q.c), (q.d, q.d)]
    
    # Calculate progress
    total_questions = Questions.query.count()
    current_question_number = len(answered_questions) + 1
    
    return render_template('question.html', 
                         form=form, 
                         q=q, 
                         title=f'Question {current_question_number}',
                         current_question=current_question_number,
                         total_questions=total_questions)


@app.route('/score')
@login_required
def score():
    """Display final quiz score"""
    if current_user.is_admin:
        flash('Admins cannot take the quiz. Please use a student account.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Only update score if quiz was actually started
    if session.get('quiz_started'):
        # Persist user's marks
        final_score = session.get('marks', 0)
        current_user.marks = final_score
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        # Clear quiz session
        session.pop('quiz_started', None)
        session.pop('answered_questions', None)
        session.pop('marks', None)
        
        # Get total possible score
        total_questions = Questions.query.count()
        max_possible_score = total_questions * 10
        
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
    student.marks = 0
    db.session.commit()
    flash(f'Reset score for {student.username}', 'success')
    return redirect(url_for('admin_students'))