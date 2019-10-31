import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from config import Config, devconfig

app = Flask(__name__)
app.config.from_object(Config)
if "-d" in sys.argv:
    app.config.from_object(devconfig)
db = SQLAlchemy(app)
auth = HTTPBasicAuth(app)


from app.routes import *
from app.models import *
db.create_all()
