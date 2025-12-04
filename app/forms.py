from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange
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
    ques = TextAreaField('Question', validators=[DataRequired()], render_kw={"rows": 3})
    a = StringField('Option A', validators=[DataRequired()])
    b = StringField('Option B', validators=[DataRequired()])
    c = StringField('Option C', validators=[DataRequired()])
    d = StringField('Option D', validators=[DataRequired()])
    ans = SelectField('Correct Answer', validators=[DataRequired()], choices=[])
    time_limit = IntegerField('Time Limit (seconds)', validators=[DataRequired(), NumberRange(min=10, max=600)], default=60)
    submit = SubmitField('Save Question')

    def __init__(self, *args, **kwargs):
        super(AdminQuestionForm, self).__init__(*args, **kwargs)
        # Dynamically set choices for correct answer based on options
        if self.a.data and self.b.data and self.c.data and self.d.data:
            self.ans.choices = [
                (self.a.data, f"A: {self.a.data}"),
                (self.b.data, f"B: {self.b.data}"),
                (self.c.data, f"C: {self.c.data}"),
                (self.d.data, f"D: {self.d.data}")
            ]
        else:
            self.ans.choices = [
                ('', 'Select correct answer after filling options')
            ]

    def validate_ques(self, ques):
        # Check if question already exists (excluding current question if editing)
        existing_q_id = getattr(self, '_edit_q_id', None)
        existing = Questions.query.filter_by(ques=ques.data).first()
        if existing and (existing_q_id is None or existing.q_id != existing_q_id):
            raise ValidationError('This question already exists.')

class EditQuestionForm(AdminQuestionForm):
    def __init__(self, question_id, *args, **kwargs):
        self._edit_q_id = question_id
        super(EditQuestionForm, self).__init__(*args, **kwargs)