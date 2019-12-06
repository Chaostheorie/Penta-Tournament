import os

# Load data from .env file if avaible
from dotenv import load_dotenv
load_dotenv()

# Config for basedir
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # App infos
    APP_VERSION = os.getenv("APP_VERSION") or "Demo"
    APP_NAME = os.getenv("APP_NAME") or "Penta Tournament"
    APP_LOCAL = "de"
    APP_PORT = 80
    TEMPLATES_AUTO_RELOAD = False
    ENV = os.getenv("ENV") or "Deploy"
    DEBUG = False
    EXPLAIN_TEMPLATE_LOADING = True
    EXPIRES = 10800
    PERMANENT_SESSION_LIFETIME = 10800
    FOOTER = False

    # Basedir
    BASEDIR = basedir

    # Secret key for sessions of flask users
    # change it before using in anything that could be attacked
    # Deploy will use "Secure Key" in the future due to issues it's not added yet
    # <https://devcenter.heroku.com/articles/securekey>
    SECRET_KEY = os.urandom(36)  # os.environ["SECRET_KEY"]

    # Database Url
    # Default is a file based sqlite3 databse in the static/databse folder
    try:
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    except KeyError:
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir,
                                                              "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-User settings
    USER_ENABLE_CHANGE_USERNAME = True
    USER_ENABLE_CHANGE_PASSWORD = True
    USER_ENABLE_REGISTER = False
    USER_USERNAME_MAX_LEN = 50
    USER_USERNAME_MIN_LEN = 3
    # the retype password field is not supported but could be used with default
    # flask user settings
    USER_REQUIRE_RETYPE_PASSWORD = False
    USER_LOGIN_TEMPLATE = "flask_user/login.html"
    USER_REGISTER_TEMPLATE = "flask_user/register.html"
    USER_PASSWORD_MAX_LEN = 256
    USER_PASSWORD_MIN_LEN = 6
    USER_EMAIL_MAX_LEN = 256
    USER_EMAIL_MIN_LEN = 5


class devconfig(Config):
    # Development specific settings
    DEBUG = True
    ENV = "development"
    USER_ENABLE_REGISTER = True
    APP_PORT = 5000

    # Settings for user data registartion validation and database settings
    # all settings must be in integers if length related
    USER_USERNAME_MAX_LEN = 100
    USER_USERNAME_MIN_LEN = 5
    USER_PASSWORD_MAX_LEN = 255
    USER_PASSWORD_MIN_LEN = 6
