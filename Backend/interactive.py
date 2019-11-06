# File for tests run with hydrogen

from datetime import date
from app import db
from app.models import *


g = games.query.filter_by(type=True).all()[1]
print(dir(g))
print(g.mastered_rel)
