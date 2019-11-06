import json
from app import app, db
from datetime import date
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

    def jsonify(self, full=False, points=False):
        """Retruns json object with user data"""
        if full:
            user = dict(
                        id=self.id, username=self.username, active=self.active,
                        e_mail=self.e_mail, description=self.description,
                        groups=[group.name for group in self.groups],
                        roles=[role.name for role in self.roles]
                        )
        else:
            user = dict(
                        id=self.id, username=self.username, active=self.active
                        )
        if points:
            user["points"] = self.get_points()
        return json.dumps(user)

    def get_points(self):
        if self.last_rated < date.today():
            return self.calculate_points()
        else:
            return self.points

    def calculate_points(self):
        """The calculation of points will cause a high load"""
        results = {1: 0, 2: 0, 3: 0, 4: 0}
        for game in self.games:
            results[game.get_points(self.id)] += 1
        self.points = results[4] * 2
        self.points -= results[1] - results[2]*0.5 - results[3]*0.5
        self.points = round(self.points)
        self.last_rated = date.today()
        db.session.commit()
        return self.points

    # User authentication information
    username = db.Column(db.String(app.config["USER_USERNAME_MAX_LEN"]),
                         nullable=False, unique=True)
    password = db.Column(db.String(app.config["USER_PASSWORD_MAX_LEN"]),
                         nullable=False)

    # User information
    e_mail = db.Column(db.String(app.config["USER_EMAIL_MAX_LEN"]))
    points = db.Column(db.Integer())
    last_rated = db.Column(db.Date())
    last_seen = db.Column(db.String(100))
    description = db.Column(db.String(300))
    custom_avatar_url = db.Column(db.String(200))

    groups = db.relationship("Groups", secondary="user_groups",
                             backref=db.backref("user", lazy="dynamic"))
    roles = db.relationship("Role", secondary="user_roles",
                            backref=db.backref("user", lazy="dynamic"))
    games = db.relationship("games", secondary="user_games",
                            backref=db.backref("User", lazy="dynamic"))

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
    tournament_games = db.relationship("games", secondary="tournament_games",
                                       backref=db.backref("played_games",
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


class matchgames(db.Model):
    __tablename__ = "match_games"

    id = db.Column(db.Integer(), primary_key=True)
    master_id = db.Column(db.Integer(),
                          db.ForeignKey("games.id", ondelete="CASCADE"))
    slave_id = db.Column(db.Integer(),
                         db.ForeignKey("games.id", ondelete="CASCADE"))


class games(db.Model):
    """Table for managing of games"""
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True)
    result = db.Column(db.JSON())  # [{"user_id": int, "points": int}]
    date = db.Column(db.Date())
    type = db.Column(db.Boolean(), server_default="1")  # 1 = Master/ Single

    @staticmethod
    def create_match(rounds=3):
        """For creating round based matches returns a match object"""
        master = games(date=date.today(), result=None, type=True)
        slaves = [games(date=date.today(), result=[], type=False)
                  for _ in range(3)]
        db.session.add(master)
        [db.session.add(game) for game in slaves]
        db.session.commit()
        db.session.flush()
        [db.session.add(matchgames(slave_id=g.id, master_id=master.id))
         for g in slaves]
        db.session.commit()
        return master

    def get_points(self, user, only_id=True):
        if only_id:
            points = [result["points"] for result in self.result
                      if result["user_id"] == user]
        else:
            points = [result["points"] for result in self.result
                      if result["user_id"] == user.id]
        return points[0]

    mastered_rel = db.relationship("games", secondary="match_games",
                                   backref=db.backref("mastered_by"),
                                   primaryjoin=(matchgames.master_id == id),
                                   secondaryjoin=(matchgames.slave_id == id))
    master_rel = db.relationship("games", secondary="match_games",
                                 backref=db.backref("master_of"),
                                 primaryjoin=(matchgames.slave_id == id),
                                 secondaryjoin=(matchgames.master_id == id))
    players = db.relationship("User", secondary="user_games",
                              backref=db.backref("players", lazy="dynamic"))

    def __repr__(self):
        return f"<game {self.id} from {self.date.strftime('%d.%m.%Y')}>"


class tournamentgames(db.Model):
    __tablename__ = "tournament_games"

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(),
                        db.ForeignKey("games.id", ondelete="CASCADE"))
    tournament_id = db.Column(db.Integer(), db.ForeignKey("tournaments.id",
                                                          ondelete="CASCADE"))




class Usergames(db.Model):
    __tablename__ = "user_games"

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(),
                        db.ForeignKey("games.id", ondelete="CASCADE"))
    user_id = db.Column(db.Integer(),
                        db.ForeignKey("user.id", ondelete="CASCADE"))
