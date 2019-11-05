from app import app, db
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer(), primary_key=True)

    def hash_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config["SECRET_KEY"], expires_in=expiration)
        refresh_token = Serializer(app.config["SECRET_KEY"],
                                   expires_in=expiration*36)
        return refresh_token.dumps({"id": self.id}), s.dumps({"id": self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return False  # valid token, but expired
        except BadSignature:
            return False  # invalid token
        user = User.query.get(data["id"])
        return user

    # User authentication information
    username = db.Column(db.String(app.config["USER_USERNAME_MAX_LEN"]),
                         nullable=False, unique=True)
    password = db.Column(db.String(app.config["USER_PASSWORD_MAX_LEN"]),
                         nullable=False)

    # User information
    e_mail = db.Column(db.String(app.config["USER_EMAIL_MAX_LEN"]))
    last_seen = db.Column(db.String(100))
    description = db.Column(db.String(300))
    custom_avatar_url = db.Column(db.String(200))

    groups = db.relationship("Groups", secondary="user_groups",
                             backref=db.backref("user", lazy="dynamic"))
    roles = db.relationship("Role", secondary="user_roles",
                            backref=db.backref("user", lazy="dynamic"))

    def __repr__(self):
        return "<User {}>".format(self.username)


# Define the Role data model
class Role(db.Model):
    __tablename__ = "role"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return "<Role {}>".format(self.name)


class Groups(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return "<Group {}>".format(self.name)


class UserRoles(db.Model):
    __tablename__ = "user_roles"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),
                        db.ForeignKey("user.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(),
                        db.ForeignKey("role.id", ondelete="CASCADE"))

    def __repr__(self):
        return "<UserRole u:{}/r:{}>".format(self.user_id, self.role_id)


class UserGroups(db.Model):
    __tablename__ = "user_groups"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),
                        db.ForeignKey("user.id", ondelete="CASCADE"))
    group_id = db.Column(db.Integer(),
                         db.ForeignKey("groups.id", ondelete="CASCADE"))

    def __repr__(self):
        return "<UserGroup u:{}/r:{}>".format(self.user_id, self.group_id)


class tournaments(db.Model):
    __tablename__ = "tournaments"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    date = db.Column(db.Date())
    duration = db.Column(db.Integer(), server_default="1", nullable=False)
    maintainer_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    maintainer = db.relationship("user")
    tournament_games = db.relationship("games", secondary="tournamentgames",
                                       backref=db.backref("game",
                                                          lazy="dynamic"))

    def get_players(self, only_id=True):
        if only_id:
            res = []
            [res.append(player.id) for player in
             [players for players in
              [game.get_players(with_res=False) for game in self.games]]
             if player.id not in res]
            return res
        else:
            res = []
            [res.append(player) for player in
             [players for players in
              [game.get_players(with_res=False) for game in self.games]]
             if player not in res]
            return res

    def __repr__(self):
        return f"<tournament {self.id} at {date.strptime('%d.%m.%Y')}>"


class games(db.Model):
    """Table for managing of games"""
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True)
    result = db.Column(db.JSON())  # [{"user_id": int, "points": int}]
    date = db.Column(db.Date())

    @staticmethod
    def create_match(rounds=3):
        """For creating round based matches returns a match object"""
        return

    def get_players(self, with_res=True):
        res = None
        if with_res:
            return [{"user": User.session.query.filter_by(res["user_id"]
                                                          ).first(),
                     "points": res["points"]} for res in self.result]
        else:
            return [User.session.query.filter_by(res["user_id"]).first()
                    for res in self.result]

    def __repr__(self):
        return f"<game {self.id} from {date.strptime('%d.%m.%Y')}>"


class tournamentgames(db.Model):
    __tablename__ = "tournamentgames"

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(),
                        db.ForeignKey("games.id", ondelete="CASCADE"))
    tournament_id = db.Column(db.Integer(), db.ForeignKey("tournaments.id"))
