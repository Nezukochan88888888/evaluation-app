from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    marks = db.Column(db.Integer, index=True)  # Keep for backward compatibility
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    session_token = db.Column(db.String(128), index=True)
    
    # New relationship for quiz scores
    scores = db.relationship('QuizScore', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Questions(db.Model):
    q_id = db.Column(db.Integer, primary_key=True)
    ques = db.Column(db.String(350), unique=True)
    a = db.Column(db.String(100))
    b = db.Column(db.String(100))
    c = db.Column(db.String(100))
    d = db.Column(db.String(100))
    ans = db.Column(db.String(100))
    time_limit = db.Column(db.Integer, default=60, nullable=False)
    quiz_category = db.Column(db.String(64), default='General', nullable=False)
    
    # Enhanced Educational Content fields
    rationalization = db.Column(db.Text)  # Explanation of the correct answer
    points = db.Column(db.Integer, default=1, nullable=False)  # Weight for harder questions
    category = db.Column(db.String(100))  # Category/Tag (e.g., "History", "Math")
    media_path = db.Column(db.String(255))  # Filename for local images (optional)
    
    # New fields for Differentiated Question Types
    question_type = db.Column(db.String(10), default='MCQ', nullable=False)  # 'MCQ', 'TF', 'Image'
    image_file = db.Column(db.String(255), nullable=True)  # Store uploaded image filenames

    def __repr__(self):
        return '<Question: {}>'.format(self.ques)


class QuizScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_category = db.Column(db.String(64), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='completed')  # 'completed' or 'incomplete'
    
    def __repr__(self):
        return '<QuizScore: {} - {} points in {} ({})>'.format(self.user_id, self.score, self.quiz_category, self.status)


class StudentResponse(db.Model):
    """Track individual question responses for distractor analysis"""
    __tablename__ = 'student_response'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.q_id', ondelete='CASCADE'), nullable=False)
    selected_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    is_correct = db.Column(db.Boolean, nullable=False)
    quiz_category = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define the relationship from the StudentResponse side with proper cascade
    question = db.relationship('Questions', backref=db.backref('responses', cascade='all, delete-orphan'))
    user = db.relationship('User', backref='user_responses')
    
    def __repr__(self):
        return '<StudentResponse: User {} answered {} for Q{} ({}correct)>'.format(
            self.user_id, self.selected_answer, self.question_id, '' if self.is_correct else 'in')
