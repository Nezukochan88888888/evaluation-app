from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    marks = db.Column(db.Integer, index=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

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

    def __repr__(self):
        return '<Question: {}>'.format(self.ques)
