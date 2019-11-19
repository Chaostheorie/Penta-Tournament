import json
from flask import render_template, g, request, abort, jsonify, make_response
from datetime import date, datetime
from sqlalchemy.exc import OperationalError
from app.models import User, Tournaments
from app.utils import requeries_json_keys, role_required
from app import app, auth, db


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/user/token", methods=["GET"])
@auth.login_required
def get_auth_token():
    refresh_token, token = g.user.generate_auth_token()
    return jsonify({"token": token.decode("ascii"),
                    "id": g.user.id,
                    "refresh_token": refresh_token.decode("ascii")})


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route("/api/user/leaderboard", methods=["GET"])
def get_leaderboard():
    limit = request.args.get("limit", default=100, type=int)
    return jsonify(User.get_leaderboard(limit=limit))


@app.route("/api/user/sign-up", methods=["POST"])
@requeries_json_keys(["username", "password"])
def new_user():
    r = request.get_json()
    username = r["username"]
    password = r["password"]
    if username is None or password is None:
        abort(400)  # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)  # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"username": user.username}), 201


@app.route("/api/tournaments/create", methods=["POST"])
@requeries_json_keys(["name", "day", "duration"])
def create_tournament():
    r = request.get_json()
    try:
        t = Tournaments(name=r["name"], maintainer_id=g.user.id,
                        duration=r["duration"],
                        day=datetime.strptime(r["day"], "%d.%m.%Y").date())
        db.session.add(t)
        db.session.commit()
    except OperationalError:
        db.session.rollback()
        return abort(400)
    except ValueError:
        db.session.rollback()
        return abort(400)
    finally:
        db.session.flush()
    return jsonify(t.jsonify())


@app.route("/api/tournaments/ongoing", methods=["GET"])
def list_ongoing_tournaments():
    limit = request.args.get("limit", default=10, type=int)
    maintainer_id = request.args.get("maintainer_id", default=None, type=int)
    if maintainer_id is not None:
        return jsonify([record.jsonify()
                        for record in Tournaments.get_active(limit, maintainer_id=maintainer_id)])
    return jsonify([record.jsonify()
                    for record in Tournaments.get_active(limit)])


@app.route("/api/tournaments/list", methods=["GET"])
def list_tournaments():
    limit = request.args.get("limit", default=10, type=int)
    maintainer_id = request.args.get("maintainer_id", default=None, type=int)
    if maintainer_id is not None:
        t = Tournaments.query.filter_by(maintainer_id=maintainer_id
                                        ).limit(limit).all()
        return jsonify([record.jsonify() for record in t])
    return jsonify([record.jsonify()
                    for record in Tournaments.query.limit(limit).all()])


@app.route("/api/tournament/<int:id>/games", methods=["GET"])
def get_tournament_games(id):
    limit = request.args.get("limit", default=None, type=int)
    active = request.args.get("ongoing", default=True)
    load_players = request.args.get("load_players", default=False)
    query = Tournaments.query.get_or_404(id).games
    if limit is not None:
        query = query.limit(limit)
    games = query.all()
    return jsonify([game.jsonify() for game in games])


@app.route("/api/tournaments/<int:id>/info", methods=["GET"])
def get_tournament_info(id):
    t = Tournaments.get_or_404(id)
    return jsonify(t.jsonify())


@app.route("/api/tournament/<int:id>/edit", methods=["POST"])
@requeries_json_keys(["duration", "date", "name", "maintainer_id"])
def edit_tournament(id):
    t = Tournaments.get_or_404(id)
    if g.user == t.maintainer:
        r = request.get_json()
        t.name = r["name"]
        t.maintainer_id = r["maintainer_id"]
        t.duration = r["duration"]
        try:
            t.date = datetime.strptime(r["day"], "%d.%m.%Y").date()
        except ValueError:
            db.session.rollback()
            return abort(400)
        except OperationalError:
            db.session.rollback()
            return abort(500)
        finally:
            db.session.commit()
            db.session.flush()
        return jsonify(t.jsonify())
    else:
        return abort(403)


@app.route("/api/tournament/<int:id>/delete", methods=["DELETE"])
def delete_tournament(id):
    t = Tournaments.get_or_404(id)
    if t.maintainer == g.user:
        try:
            db.session.remove(t)
        except OperationalError:
            db.session.rollback()
            return abort(500)
        finally:
            db.session.commit(t)
    else:
        return abort(403)
    return jsonify({"result": "success"}), 200


@app.route("/api/tournament/<int:id>/games", methods=["GET"])
def get_games(id):
    t = Tournaments.get_or_404(id)
    limit = request.args.get("limit", default=10, type=int)


@app.route("/api/gui/changelog")
def get_changelog():
    changelog = """
    That's some awesome content
        - Point 1
        - Some new feature
    """
    return changelog, 200


@auth.error_handler
def unauthorized():
    return make_response(jsonify({"error": "Unauthorized access"}), 401)


@app.before_request
def before_request_hook():
    """Hook for signal if maintenance's ongoing"""
    if app.maintenance:
        e = "The server is currently unable to handle the request due to a \
             temporary overloading or maintenance of the server."
        return make_response(jsonify({"error": e}), 503)
    else:
        return
