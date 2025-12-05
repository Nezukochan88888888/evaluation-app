from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange, Optional
from app.models import User, Questions

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=(DataRequired(), Email()))
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', 
                validators=(DataRequired(), EqualTo('password')))
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exists')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already exists.')

class QuestionForm(FlaskForm):
    options = RadioField('Options: ', validators=[DataRequired()])
    submit = SubmitField('Next')

class AdminQuestionForm(FlaskForm):
    # Question Type Selection
    question_type = SelectField('Question Type', 
                               choices=[('MCQ', 'Multiple Choice'), ('TF', 'True/False'), ('Image', 'Image-based')],
                               default='MCQ', validators=[DataRequired()])
    
    ques = TextAreaField('Question', validators=[DataRequired()], render_kw={"rows": 3})
    
    # Options (C and D will be optional for True/False)
    a = StringField('Option A', validators=[DataRequired()])
    b = StringField('Option B', validators=[DataRequired()])
    c = StringField('Option C')  # Optional for TF questions
    d = StringField('Option D')  # Optional for TF questions
    
    ans = SelectField('Correct Answer', validators=[DataRequired()], choices=[])
    quiz_category = StringField('Quiz Category', validators=[DataRequired()], default='General')
    time_limit = IntegerField('Time Limit (seconds)', validators=[DataRequired(), NumberRange(min=10, max=600)], default=60)
    
    # Image upload field
    image = FileField('Question Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Only JPG and PNG images are allowed!')
    ])
    
    # Enhanced Educational Content fields
    rationalization = TextAreaField('Explanation of Correct Answer', render_kw={"rows": 3, "placeholder": "Explain why this is the correct answer..."})
    points = IntegerField('Points (Question Weight)', validators=[NumberRange(min=1, max=10)], default=1)
    category = StringField('Subject Category', render_kw={"placeholder": "e.g., History, Math, Science"})
    media_path = StringField('Image Filename (optional)', render_kw={"placeholder": "e.g., image.jpg (place in static/images/)"})
    
    submit = SubmitField('Save Question')

    def __init__(self, *args, **kwargs):
        super(AdminQuestionForm, self).__init__(*args, **kwargs)
        # Dynamically set choices for correct answer based on question type and options
        self.ans.choices = [('', 'Select correct answer after filling options')]

    def validate_ques(self, ques):
        # Check if question already exists (excluding current question if editing)
        existing_q_id = getattr(self, '_edit_q_id', None)
        existing = Questions.query.filter_by(ques=ques.data).first()
        if existing and (existing_q_id is None or existing.q_id != existing_q_id):
            raise ValidationError('This question already exists.')
    
    def validate_c(self, c):
        # Option C is required for MCQ and Image questions
        if self.question_type.data in ['MCQ', 'Image'] and not c.data:
            raise ValidationError('Option C is required for Multiple Choice and Image-based questions.')
    
    def validate_d(self, d):
        # Option D is required for MCQ and Image questions
        if self.question_type.data in ['MCQ', 'Image'] and not d.data:
            raise ValidationError('Option D is required for Multiple Choice and Image-based questions.')

class EditQuestionForm(AdminQuestionForm):
    def __init__(self, question_id, *args, **kwargs):
        self._edit_q_id = question_id
        super(EditQuestionForm, self).__init__(*args, **kwargs)