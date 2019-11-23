import sys
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from config import Config, devconfig

app = Flask(__name__)
app.config.from_object(Config)
if "-d" in sys.argv:
    app.config.from_object(devconfig)

db = SQLAlchemy(app, session_options={"autoflush": True}), engine_options={"executemany_mode": "batch"})
auth = HTTPBasicAuth()

cron = BackgroundScheduler(daemon=True)
# Explicitly kick off the background thread
cron.start()
app.maintenance = False

import app.utils as utils
from app.utils.maintenance import maintenance
cron.add_job(maintenance, "date", run_date=utils.tomorrow())


# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))


from app.routes import *
from app.models import *
db.create_all()

with open("banner.txt") as f:
    print(f.read())
