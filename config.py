import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable the development mode.
FLASK_ENV = os.getenv('FLASK_ENV')
# Enable debug mode.
DEBUG = True

# secret key for CSRF token
WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY')
# desable globally CSRF token
WTF_CSRF_ENABLED = False

# Connect to the database and DATABASE URL
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = False
