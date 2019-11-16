# File for tests run with hydrogen

from app.models import tournaments, User
from datetime import date


u = User.query.first()
tournaments.create_tournament("Test", u, date.today())
