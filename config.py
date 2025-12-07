import os
import sys

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (PyInstaller), the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    # For the database, we want it next to the executable, not in the temp folder.
    basedir = os.path.dirname(sys.executable)
else:
    basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    QUES_PER_PAGE = 1
    # WTF_CSRF_ENABLED = True # Enabled by default in Flask-WTF
    
    # Fix for admin_questions Internal Server Error - URL building configuration
    SERVER_NAME = None  # Let Flask auto-detect from request
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'