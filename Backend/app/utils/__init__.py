from app import db, cron
from app.models import Role
from datetime import date, timedelta
from flask import request, abort, g
from simplejson.errors import JSONDecodeError
import functools
import json


def requeries_json_keys(keys):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json(force=True, cache=True)
            except JSONDecodeError:
                return abort(400)
            if len([rkey for rkey in keys
                    if rkey not in data]) >= 1:
                return abort(400)
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator


def role_required(names):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            roles = [Role.query.filter_by(name=name).first() for name in names]
            if len([role for role in roles if role not in g.user.roles]) >= 1:
                return abort(403)
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator


def vacuum_db():
    """
    Runs vacuum at Database
    https://stackoverflow.com/questions/2128336/what-does-it-mean-to-vacuum-a-database
    """
    with db.engine.begin() as conn:
        conn.execute("VACUUM")


def tomorrow():
    """Returns date object for tomorrow"""
    return date.today() + timedelta(days=1)


def schuedle_maintenance():
    """schuedles Maintenance"""
    return cron.add_job(utils.maintenance, "date", date=utils.tomorrow())
