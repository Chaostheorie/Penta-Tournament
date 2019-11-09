# File for tests run with hydrogen

from app.models import tournaments

t = tournaments.query.first()
t.jsonify()

t.get_players()
