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

from flask import json

import bcrypt

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

db = SessionLocal()
metadata = MetaData()


def generate_uuid():
    return str(uuid4())


class Connections(Base):
    __tablename__ = "connections"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    user_id = Column(String(255), ForeignKey("users.id"))
    connected_user_id = Column(String(255), ForeignKey("users.id"))
    connected_user = relationship("User", foreign_keys=[connected_user_id], back_populates="connected_to")
    user = relationship("User", foreign_keys=[user_id], back_populates="connections")
    connection_type = Column(Enum('clients', 'colleagues', 'mentors'),
                             server_default='colleagues')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {'user_id': self.user_id,
                'connection_type': self.connection_type,
                'connection': self.connected_user.username,
                'last_seen': self.last_modified,
                'added_at': self.created_at,
                }

    def to_json(self):
        return json.loads(json.dumps(self.to_dict(), default=str))


class User(Base):
    """User model for all classes."""
    __tablename__ = "users"

    id = Column(String(255), primary_key=True, default=generate_uuid, nullable=False)
    username = Column(String(64), index=True, unique=True, nullable=False)
    email = Column(String(20), index=True, unique=True, nullable=False)
    password = Column(String(500), nullable=True)
    assigned_tasks = relationship("Task", secondary="assigned_tasks")
    profile = relationship("Profile", uselist=False, back_populates="user")
    connections = relationship("Connections", back_populates="user",
                               foreign_keys=[Connections.user_id])
    connected_to = relationship("Connections", back_populates="connected_user",
                                foreign_keys=[Connections.connected_user_id])
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        """
            The to_dict function is used to return a
            dict representation of the object
            :return: The dict formatted object.
        """
        return {'email': self.email,
                'created': self.created_at,
                'username': self.username,
                'last_seen': self.last_modified
                }

    def to_json(self):
        """
            The to_json function is used to return a
            json representation of the object
            :return: The json formatted object.
        """

        return json.loads(json.dumps(self.to_dict(), default=str))

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
    """Data model for User profile."""

    __tablename__ = "profiles"

    id = Column(String(255), primary_key=True, default=generate_uuid)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="profile")
    about_me = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def avatar(self, size):
        """
            It  returns  an image generted by encoding user email
            from the gravatar website url
            :return: An avatar icon.
        """
        img_avatar = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            img_avatar, size)

    def to_dict(self):
        """
            It returns a
            dict representation of the object
            :return: The dict formatted object.
        """
        return {
            'id': self.id,
            'username': self.user.username,
            'about_me': self.about_me,
            'last_seen': self.last_modified
        }

    def to_json(self):
        """
            It returns a
            json representation of the object
            :return: The json formatted object.
        """
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
        """
            It returns a
            dict representation of the object
            :return: The dict formatted object.
        """
        return {'id': self.id,
                'user_id': self.user_id,
                'title': self.title,
                'task_name': self.task_name,
                'month': self.month,
                }

    def to_json(self):
        """
            It returns a
            json representation of the object
            :return: The json formatted object.
        """
        return json.loads(json.dumps(self.to_dict(), default=str))


class AssignedTasks(Base):
    __tablename__ = 'assigned_tasks'
    user_id = Column(String(255), ForeignKey('users.id'), primary_key=True)
    task_id = Column(String(255), ForeignKey('tasks.id'), primary_key=True)
    subtask_id = Column(String(255), ForeignKey('subtasks.id'))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        """
            It returns a
            dict representation of the object
            :return: The dict formatted object.
        """

        user = db.query(User).filter(User.id == self.user_id).first()
        return {'user_id': self.user_id,
                'user': user.username if user else None,
                'task_id': self.task_id,
                'subtask_id': self.subtask_id,
                'assigned_at': self.assigned_at,

                }

    def to_json(self):
        """
            It returns a
            json representation of the object
            :return: The json formatted object.
        """
        return json.loads(json.dumps(self.to_dict(), default=str))


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
        """
            It returns a
            dict representation of the object
            :return: The dict formatted object.
        """
        return {'task_id': self.task_id,
                'due_date': self.due_date,
                'created': self.created_at,
                'title': self.title,
                'content': self.content,
                'assigned_to': self.assigned_to,
                'last_modified': self.last_modified,
                'status': self.status
                }

    def to_json(self):
        """
            It returns a
            json representation of the object
            :return: The json formatted object.
        """
        return json.loads(json.dumps(self.to_dict(), default=str))

    # def __str__(self):
    #     return json.dumps(dict(self), cls=CustomEncoder, ensure_ascii=False)
    #
    # def __repr__(self):
    #     return self.__str__()

# add connection type to schema as enum
