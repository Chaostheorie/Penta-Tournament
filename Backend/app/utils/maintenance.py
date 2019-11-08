import app.utils as utils
from app import app, cron
from app.models import User


def maintenance():
    """maintenance tasks and daily schuedled tasks"""
    app.maintenance = True
    [user.calculate_points() for user in User.query.all()]
    top_100 = User.query.order_by(User.points.desc()).all().limit(100)
    top_100_role = Role.query.filter_by(name="Top 100").first()
    [user.add_role(top_100_role) for user in top_100]
    utils.vacuum_db()
    app.maintenance = False
    utils.schuedle_maintenance()
