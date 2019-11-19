import json
import logging
import warnings
from app import app, db
from datetime import date, timedelta
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

    def add_role(self, role):
        db.session.add(UserRoles(user_id=self.id, role_id=role.id))
        db.session.commit()
        return

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return False  # valid token, but expired
        except BadSignature:
            return False  # invalid token
        user = User.query.get(data["id"])
        return user

    def jsonify(self, full=False, points=False):
        """Returns json object with user data"""
        if full:
            user = dict(
                        id=self.id, username=self.username,
                        e_mail=self.e_mail, description=self.description,
                        groups=[group.name for group in self.groups],
                        roles=[role.name for role in self.roles]
                        )
        else:
            user = dict(id=self.id, username=self.username)
        if points:
            user["points"] = self.points
        return json.dumps(user)

    def calculate_points(self):
        """The calculation of points will cause a relatively high load"""
        results = {1: 0, 2: 0, 3: 0, 4: 0}
        for game in self.games.all():
            results[game.get_points(self.id)] += 1
        self.points = results[4] * 2
        self.points -= results[1] - results[2]*0.5 - results[3]*0.5
        self.points = round(self.points)
        self.last_rated = date.today()
        db.session.commit()
        return self.points

    @staticmethod
    def get_leaderboard(limit=100):
        return [user.jsonify(points=True)
                for user in User.query.order_by(User.points.desc()
                                                ).limit(limit).all()]

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

    Tournaments = db.relationship("Tournaments", backref="maintainer",
                                  lazy="dynamic")
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


class Tournaments(db.Model):
    __tablename__ = "tournaments"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50))
    date = db.Column(db.Date())
    duration = db.Column(db.Integer(), server_default="1", nullable=False)
    maintainer_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    tournament_games = db.relationship("Games", secondary="tournament_games",
                                       backref=db.backref("played_games",
                                                          lazy="dynamic"))

    def active(self):
        if date.today() <= self.date or \
           self.date+timedelta(days=self.duration) >= date.today():
            return True
        else:
            return False

    def find_pair(self, player, init_match=False):
        """Select two players for a game/ match"""
        not_matched = [enemy for enemy in
                       [part for part in self.participants]
                       if player not in participant.get_games(self).players]
        try:
            not_matched.remove(player)
        except ValueError:
            warning.warn("Player is not participating in this tournament")
        if len(not_matched) == 1:
            return not_matched[0]
        elif len(not_matched) > 1:
            return not_matched.sort("points")
        else:
            pass

    def add_player(self, player):
        if TournamentPlayers.query.filter_by(user_id=player.id,
                                             tournament_id=self.id
                                             ).first() is None:
            db.session.add(TournamentPlayers(user_id=player.id,
                                             tournament_id=self.id))
            db.session.commit()
        else:
            warning.warn("TournamentPlayers Entry was already existing")

    @staticmethod
    def create_tournament(name, maintainer, date, duration=1, players=None):
        new_tournament = Tournaments(name=name, maintainer_id=maintainer.id,
                                     date=date, duration=duration)
        db.session.add(new_tournament)
        if players is not None:
            db.session.flush()
            [new_tournament.add_player(player) for player in players]
        db.session.commit()

    @staticmethod
    def get_active(limit=10, tournaments=None):
        if tournaments is not None:
            return [record for record in tournaments
                    if record.active() is True][:limit+1]
        return [record for record in Tournaments.query.all()
                if record.active() is True][:limit+1]

    def jsonify(self, game_ids=False):
        entry = dict(name=self.name, date=self.date.strftime("%m.%d.%Y"),
                     duration=self.duration, maintainer_id=self.maintainer_id,
                     maintainer_username=self.maintainer.username, id=self.id,
                     participants=len(self.participants), active=self.active())
        if game_ids:
            entry["game_ids"] = [game.id for game in games]
        return json.dumps(entry)

    participants = db.relationship("User", secondary="tournament_players",
                                   backref=db.backref("participating_in",
                                                      lazy="dynamic"))

    def __repr__(self):
        return f"<tournament {self.id} at {self.date.strftime('%d.%m.%Y')}>"


class matchgames(db.Model):
    __tablename__ = "match_games"

    id = db.Column(db.Integer(), primary_key=True)
    master_id = db.Column(db.Integer(),
                          db.ForeignKey("games.id", ondelete="CASCADE"))
    slave_id = db.Column(db.Integer(),
                         db.ForeignKey("games.id", ondelete="CASCADE"))


class Games(db.Model):
    """Table for managing of games"""
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True)
    result = db.Column(db.JSON())  # [{"user_id": int, "points": int}]
    date = db.Column(db.Date())
    duration = db.Column(db.Integer())  # Measured in minutes
    type = db.Column(db.Boolean(), server_default="1")  # 1 = Master/ Single

    @staticmethod
    def create_match(rounds=3):
        """For creating round based matches returns a match object"""
        master = Games(date=date.today(), result=None, type=True)
        slaves = [Games(date=date.today(), result=[], type=False)
                  for _ in range(3)]
        db.session.add(master)
        [db.session.add(game) for game in slaves]
        db.session.commit()
        db.session.flush()
        [db.session.add(matchgames(slave_id=game.id, master_id=master.id))
         for game in slaves]
        db.session.commit()
        return master

    @property
    def player_ids(self):
        return [player.id for player in self.players]

    def get_points(self, user, only_id=True):
        if only_id:
            points = [result["points"] for result in self.result
                      if result["user_id"] == user]
        else:
            points = [result["points"] for result in self.result
                      if result["user_id"] == user.id]
        return points[0]

    def jsonify(self, load_players=False):
        res = dict(id=self.id, result=self.result,
                   type=self.type, date=self.date)
        if load_players:
            players = [User.get(data["user_id"]).jsonify()
                       for data in self.result]
            for i in range(len(res["result"])):
                res[i]["result"] = dict(points=res["result"][i]["points"],
                                        user=players[i])
        return res

    mastered_rel = db.relationship("Games", secondary="match_games",
                                   backref=db.backref("mastered_by"),
                                   primaryjoin=(matchgames.master_id == id),
                                   secondaryjoin=(matchgames.slave_id == id))
    master_rel = db.relationship("Games", secondary="match_games",
                                 backref=db.backref("master_of"),
                                 primaryjoin=(matchgames.slave_id == id),
                                 secondaryjoin=(matchgames.master_id == id))
    tournaments = db.relationship("Tournaments", secondary="tournament_games",
                                  backref=db.backref("games", lazy="dynamic"))
    players = db.relationship("User", secondary="user_games",
                              backref=db.backref("games", lazy="dynamic"))

    def __repr__(self):
        return f"<game {self.id} from {self.date.strftime('%d.%m.%Y')}>"


class TournamentGames(db.Model):
    __tablename__ = "tournament_games"

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(),
                        db.ForeignKey("games.id", ondelete="CASCADE"))
    tournament_id = db.Column(db.Integer(), db.ForeignKey("tournaments.id",
                                                          ondelete="CASCADE"))


class UserGames(db.Model):
    __tablename__ = "user_games"

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(),
                        db.ForeignKey("games.id", ondelete="CASCADE"))
    user_id = db.Column(db.Integer(),
                        db.ForeignKey("user.id", ondelete="CASCADE"))


class TournamentPlayers(db.Model):
    __tablename__ = "tournament_players"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),
                        db.ForeignKey("user.id", ondelete="CASCADE"))
    tournament_id = db.Column(db.Integer(), db.ForeignKey("tournaments.id",
                                                          ondelete="CASCADE"))
