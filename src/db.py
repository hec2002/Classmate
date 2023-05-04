import datetime
import hashlib
import os

import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """
    Class representing Users
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    netid = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password_digest = db.Column(db.String, nullable=False)
    session_token = db.Column(db.String, nullable=False)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False)
    schedule = db.relationship("Schedule")

    def __init__(self, **kwargs):
        """
        Initialize User object.
        """
        self.name = kwargs.get("name")
        self.netid = kwargs.get("netid")
        self.email = kwargs.get("email")
        self.password_digest = bcrypt.hashpw(kwargs.get(
            "password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()

    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

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
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "netid": self.netid,
            "friends": [friend.serialize for friend in self.friends]
        }


class Friendship(db.Model):
    """
    Class representing friendships between users.
    """
    __tablename__ = "friendship"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    timestamp = db.Column(db.String, nullable=False)
    sender_id = db.Column(db.String, db.ForeignKey(
        "user.netid"), nullable=False)
    reciever_id = db.Column(db.String, db.ForeignKey(
        "user.netid"), nullable=False)
    accepted = db.Column(db.Integer)
    friend = db.relationship("User", backref=db.backref("friends", cascade="all, delete-orphan"), foreign_keys=[reciever_id])

    def __init__(self, **kwargs):
        self.timestamp = kwargs.get("timestamp")
        self.sender_id = kwargs.get("sender_id")
        self.reciever_id = kwargs.get("receiver_id")
        self.accepted = kwargs.get("accepted")

    def serialize(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.reciever_id,
            "accepted": bool(self.accepted)
        }


class Schedule(db.Model):
    """
    Class representing Schedules
    """
    __tablename__ = "schedule"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    classes = db.relationship("Class")

    def __int__(self, **kwargs):
        self.user_id = kwargs.get("user_id")

    def serialize(self):
        return {
            "id": self.id,
            "user": self.user_id,
            "classes": [c.serialize for c in self.classes]
        }


class Class(db.Model):
    __tablename__ = "class"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    typ = db.Column(db.String, nullable=False)
    start_hour= db.Column(db.String, nullable=False)
    start_minute = db.Column(db.String, nullable=False)
    start_period = db.Column(db.String, nullable=False)
    end_hour = db.Column(db.String, nullable=False)
    end_minute = db.Column(db.String, nullable=False)
    end_period = db.Column(db.String, nullable=False)
    days = db.Column(db.String, nullable=False)
    schedule = db.Column(db.Integer, db.ForeignKey(
        "schedule.id"), nullable=False)

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.code = kwargs.get("code")
        self.typ = kwargs.get("type")
        self.start_hour = kwargs.get("start_hour")
        self.start_minute= kwargs.get("start_minute")
        self.start_period = kwargs.get("start_period")
        self.end_hour = kwargs.get("end_hour")
        self.end_minute = kwargs.get("end_minute")
        self.end_period = kwargs.get("end_period")
        self.days = kwargs.get("days")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_hour + ":" + self.start_minute + " " + self.start_period,
            "end_time": self.end_hour + ":" + self.end_minute + " " + self.end_period,
            "days": self.days,
            "type": self.typ,
            "schedule": self.schedule
        }
