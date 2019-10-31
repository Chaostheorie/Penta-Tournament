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
        return check_password_hash(password, self.password)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config["SECRET_KEY"], expires_in=expiration)
        return s.dumps({"id": self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
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
