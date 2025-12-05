import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    QUES_PER_PAGE = 1
    WTF_CSRF_ENABLED = False  # Disable CSRF temporarily for quiz functionality
    
    # Fix for admin_questions Internal Server Error - URL building configuration
    SERVER_NAME = None  # Let Flask auto-detect from request
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'