from datetime import datetime, timezone
from uuid import uuid4
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from database import Base, SessionLocal
from hashlib import md5
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, String, DateTime,
    Integer, String, ForeignKey, Column, Enum
)
from sqlalchemy.sql import func
import bcrypt
from flask import jsonify

db = SessionLocal()


def generate_uuid():
    return str(uuid4())


class User(Base):
    """Data model for user accounts."""

    __tablename__ = "users"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    username = Column(String(64), index=True, unique=True, nullable=False)
    email = Column(String(20), index=True, unique=True, nullable=False)
    password = Column(String(500), nullable=True)
    created = Column(DateTime, default=datetime.utcnow)
    assignees = relationship("Assignee", back_populates="assigner")
    tasks = relationship("Task", back_populates="user")
    profile = relationship("Profile", uselist=False, back_populates="user")
    last_seen = Column(DateTime, default=datetime.utcnow,
                       onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        """
        The function takes in a dictionary of keyword arguments
        and assigns the values to the class
        attributes
        """
        self.username = kwargs.get("username")
        self.email = kwargs.get("email")
        self.password = kwargs.get("password")

    def to_dict(self):
        return {
            'email': self.email,
            'created': self.created
        }

    @classmethod
    def get_by_id(cls, user_id):
        return db.query(cls).filter(cls.id == user_id).first()

    def get_id(self):
        return self.id

    def __repr__(self):
        """
        The __repr__ function is used to return a
        string representation of the object
        :return: The username of the user.
        """
        return "<User {}>".format(self.username)

    def hash_password(self):
        """
        It takes the password that the user has entered, hashes it,
        and then stores the hashed password in
        the database
        """
        pass
        # pwd_bytes = bytes(self.password, "utf-8")
        # salt = bcrypt.gensalt()
        # self.password = bcrypt.hashpw(pwd_bytes, salt)

    def check_password(self, password):
        """
        It takes a plaintext password, hashes it, and
        compares it to the hashed password in the database
        :param password: The password to be hashed
        :return: The password is being returned.
        """
        return self.password == password
        # password_to_check_bytes = password.encode()
        # return bcrypt.checkpw(password_to_check_bytes, self.password)


class Assignee(Base):
    __tablename__ = 'assignees'

    id = Column(String(255), primary_key=True, default=generate_uuid)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    task_id = Column(ForeignKey("tasks.id"), nullable=False)
    assigner = relationship('User', back_populates='assignees')
    created_at = Column(DateTime, default=datetime.utcnow)


class Profile(Base):
    """Data model for user profile."""

    __tablename__ = "profiles"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="profile")
    about_me = Column(String(50), nullable=True)
    last_modified = Column(DateTime, default=datetime.utcnow)
    created = Column(DateTime, default=datetime.utcnow)

    def avatar(self, size):
        img_avatar = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def to_dict(self):
        return {
            'username': self.user.username,
            'about_me': self.about_me,
            'last_seen': self.last_seen
        }


class Task(Base):
    """Data model for user tasks."""

    __tablename__ = "tasks"

    id = Column(String(255), primary_key=True, default=generate_uuid)  # named ref tasks.uid
    user_id = Column(ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="tasks")
    title = Column(String(255), nullable=False)
    name = Column(String(20), index=True, unique=True, nullable=False)
    subtasks = relationship("Subtask")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow)
    month = Column(Integer)


class Subtask(Base):
    """Data model for user tasks."""

    __tablename__ = "subtasks"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    due_date = Column(DateTime)
    task = relationship("Task", back_populates="subtasks")
    title = Column(String(255), nullable=False)
    task_id = Column(ForeignKey("tasks.id"), nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    assigned_to = Column(String(20), ForeignKey("users.username"))
    content = Column(String(30), nullable=True)
    status = Column(Enum('unassigned', 'assigned', 'started',
                         'inprogress', 'done', name='tasks_status'),
                    server_default='unassigned')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

# class BlacklistToken(Base):
#     __tablename__ = "blacklist_tokens"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     jti = Column(String(120), unique=True, nullable=False)
#     blacklisted_on = Column(DateTime, default=datetime.now())

#     def __init__(self, jti):
#         self.jti = jti

#     def __repr__(self):
#         return '<id: token: {}'.format(self.jti)
