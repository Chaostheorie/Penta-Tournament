import json
from flask import render_template, g, request, abort, jsonify, make_response
from app.models import User
from app import app, auth, db


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/user/token", methods=["GET"])
@auth.login_required
def get_auth_token():
    refresh_token, token = g.user.generate_auth_token()
    return jsonify({"token": token.decode("ascii"),
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


@app.route("/api/user/sign-up", methods=["POST"])
def new_user():
    r = json.loads(request.get_json())
    if "username" not in r.keys() or "password" not in r.keys():
        abort(400)  # Missing keys
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
@auth.login_required
def create_tournament():
    r = json.loads(request.get_json())
    return


@auth.error_handler
def unauthorized():
    return make_response(jsonify({"error": "Unauthorized access"}), 401)
