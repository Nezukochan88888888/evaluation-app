from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Auth
login = LoginManager(app)
login.login_view = 'login'

# Admin
admin = Admin(app, name='Exam Admin')

from app import routes
from app import cli
