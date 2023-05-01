import datetime
import hashlib
import os

import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

user_to_token = db.Table("user_to_token", 
db.Column("course_id", db.Integer, db.ForeignKey("course.id")), 
db.Column("user_id", db.Integer, db.ForeignKey("user.id")))

class User(db.Model):
    """
    Class representing Users
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullabe=False)
    bio = db.Column(db.String)
    email = db.Column(db.String, nullable=False)
    password_digest = db.Column(db.String, nullable=False)
    session_token = db.Column(db.String, nullable=False)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False)

    def __init__(self, **kwargs):
        """
        Initialize User object.
        """
        self.name = kwargs.get("name")
        self.bio = kwargs.get("bio")
        self.email = kwargs.get("email")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()

    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.random(64)).hexdigest()
    
    def renew_session(self):
        """
        Creates new session token. Sets expiration time to be a day from now. 
        Creates a new update token. 
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a user
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token

    def serialize(self):
        return {
            "name" : self.name,
            "email" : self.email
        }

class Schedule(db.Model):
    """
    Class representing Schedules
    """
    __tablename__ = "schedule"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    classes = db.Column(db.String, nullable=False)
    token = db.relationship("Token", secondary=user_to_token)
