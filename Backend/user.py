from app import db
from datetime import date
from app.models import *

t = Tournaments(name="My Tournament", duration=4, date=date.today())
u = User(username="joshua")
u.hash_password("Test1")
r = Role(name="admin")
ur = UserRoles(user_id=1, role_id=1)
g = Games(result=[{"user_id": 1, "points": 3}], date=date.today())
tg = TournamentGames(tournament_id=1, game_id=1)
db.session.add(t)
db.session.add(tg)
db.session.add(u)
db.session.add(g)
db.session.add(ur)
db.session.commit()
db.session.flush()
