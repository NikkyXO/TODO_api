from datetime import datetime, timezone
from uuid import uuid4
import json
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from database import Base, SessionLocal
from hashlib import md5
from sqlalchemy.orm import relationship, backref
from sqlalchemy import (
    Column, String, DateTime, Table,
    Integer, String, ForeignKey, Column, Enum, MetaData
)

from sqlalchemy.sql import func
import bcrypt

db = SessionLocal()
metadata = MetaData()


def generate_uuid():
    return str(uuid4())


class User(Base):
    """User model for all classes."""
    __tablename__ = "users"

    id = Column(String(255), primary_key=True, default=generate_uuid, nullable=False)
    username = Column(String(64), index=True, unique=True, nullable=False)
    email = Column(String(20), index=True, unique=True, nullable=False)
    password = Column(String(500), nullable=True)
    assigned_tasks = relationship("Task", secondary="assigned_tasks")
    profile = relationship("Profile", uselist=False, back_populates="user")
    connections = relationship("Connections", back_populates="connected_user")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # def __init__(self, **kwargs):
    #     """
    #     The function takes in a dictionary of keyword arguments
    #     and assigns the values to the class
    #     attributes
    #     """
    #     self.username = kwargs.get("username")
    #     self.email = kwargs.get("email")
    #     self.password = kwargs.get("password")

    def to_dict(self):
        return {'email': self.email,
                'created': self.created_at,
                'username': self.username,
                'assigned_tasks': self.assigned_tasks,
                'last_seen': self.last_modified}

    def to_json(self):
        return json.loads(json.dumps(self.to_dict(), default=str))

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


class Profile(Base):
    """Data model for user profile."""

    __tablename__ = "profiles"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="profile")
    about_me = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def avatar(self, size):
        img_avatar = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            img_avatar, size)

    def to_dict(self):
        """returns a dictionary containing all keys/values of the instance"""
        return {
            'id': self.id,
            'username': self.user.username,
            'about_me': self.about_me,
            'last_seen': self.last_modified
        }

    def to_json(self):
        return json.loads(json.dumps(self.to_dict(), default=str))


class Task(Base):
    """Data model for user tasks."""

    __tablename__ = "tasks"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, name='title')
    task_name = Column(String(255), name='task_name')
    subtasks = relationship("Subtask")
    assigned_users = relationship('User', secondary='assigned_tasks', back_populates='assigned_tasks')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    month = Column(Integer, default=func.month(created_at), name='month')

    def to_dict(self):
        return {'id': self.id,
                'user_id': self.user_id,
                'title': self.title,
                'task_name': self.task_name,
                'subtasks': self.subtasks,
                'assigned_users': self.assigned_users,
                'month': self.month}

    def to_json(self):
        return json.loads(json.dumps(self.to_dict(), default=str))


# assigned_tasks = Table('assigned_tasks', Base.metadata,
#                        Column('user_id', String(255), ForeignKey('users.id')),
#                        Column('task_id', String(255), ForeignKey('tasks.id')),
#                        Column('subtask_id', String(255), ForeignKey('subtasks.id')))


class AssignedTasks(Base):
    __tablename__ = 'assigned_tasks'
    user_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    task_id = Column(String(255), ForeignKey('tasks.id'), primary_key=True)
    subtask_id = Column(String(255), ForeignKey('subtasks.id'))


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
    content = Column(String(255), nullable=True)
    status = Column(Enum('unassigned', 'assigned', 'started',
                         'in-progress', 'done', 'null', name='tasks_status'),
                    server_default='unassigned')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {'task_id': self.task_id,
                'due_date': self.due_date,
                'created': self.created_at.isoformat(),
                'title': self.title,
                'content': self.content,
                'assigned_to': self.assigned_to,
                'last_seen': self.last_modified.isoformat()
                }

    def to_json(self):
        return json.loads(json.dumps(self.to_dict(), default=str))


class Connections(Base):
    __tablename__ = "connections"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    user_id = Column(String(255), ForeignKey("users.id"))
    connected_user = relationship("User", back_populates="connections")
    connection_type = Column(Enum('clients', 'colleagues', 'mentors'),
                             server_default='colleagues')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {'connection_type': self.connection_type,
                'connected_user': self.connected_user,
                'last_seen': self.last_modified,
                'addd_at': self.created_at,
                }

    def to_json(self):
        return json.loads(json.dumps(self.to_dict(), default=str))
