from datetime import datetime
import uuid
from settings.database import Base, SessionLocal
from hashlib import md5
from sqlalchemy.orm import relationship
from sqlalchemy import (
    DateTime, Integer, String, ForeignKey, Column, Enum, MetaData
)
from sqlalchemy.sql import func

time = "%Y-%m-%dT%H:%M:%S.%f"

db = SessionLocal()
metadata = MetaData()


class BaseModel:
    """The BaseModel class from which future classes will be derived"""
    id = Column(String(60), primary_key=True, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        """Initialization of the base model"""
        if kwargs:
            for key, value in kwargs.items():
                if key != "__class__":
                    setattr(self, key, value)
            if kwargs.get("created_at", None) and type(self.created_at) is str:
                self.created_at = datetime.strptime(kwargs["created_at"], time)
            else:
                self.created_at = datetime.utcnow()
            if kwargs.get("updated_at", None) and type(self.updated_at) is str:
                self.updated_at = datetime.strptime(kwargs["updated_at"], time)
            else:
                self.updated_at = datetime.utcnow()
            if kwargs.get("id", None) is None:
                self.id = str(uuid.uuid4())
        else:
            self.id = str(uuid.uuid4())
            self.created_at = datetime.utcnow()
            self.updated_at = self.created_at

    def __str__(self):
        """String representation of the BaseModel class"""
        return f"{self.__class__.__name__}, {self.id}, {self.__dict__}"

    def save(self):
        """updates the attribute 'updated_at' with the current datetime"""
        self.updated_at = datetime.utcnow()
        db.add(self)
        db.commit()

    def to_dict(self):
        """returns a dictionary containing all keys/values of the instance"""
        new_dict = self.__dict__.copy()
        if "created_at" in new_dict:
            new_dict["created_at"] = new_dict["created_at"].strftime(time)
        if "updated_at" in new_dict:
            new_dict["updated_at"] = new_dict["updated_at"].strftime(time)
        new_dict["__class__"] = self.__class__.__name__
        if "_sa_instance_state" in new_dict:
            del new_dict["_sa_instance_state"]
        if "password" in new_dict:
            del new_dict["password"]
        return new_dict


class Connections(BaseModel, Base):
    __tablename__ = "connections"

    user_id = Column(String(60), ForeignKey("users.id", ondelete="CASCADE"))
    connected_user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    connected_user = relationship("User", foreign_keys=[connected_user_id], back_populates="connected_to")
    user = relationship("User", foreign_keys=[user_id], back_populates="connections")
    connected_name = Column(String(64), ForeignKey("users.username", ondelete="CASCADE"))
    connection_type = Column(Enum('clients', 'colleagues', 'mentors'), server_default='colleagues')

    def __init__(self, *args, **kwargs):
        """initializes connections"""
        super().__init__(*args, **kwargs)


class User(BaseModel, Base):
    """User model for all classes."""
    __tablename__ = "users"

    username = Column(String(64), index=True, unique=True, nullable=False)
    email = Column(String(20), index=True, unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    assigned_tasks = relationship("Task", secondary="assigned_tasks")
    profile = relationship("Profile", uselist=False, back_populates="user", cascade="all, delete, delete-orphan")
    connections = relationship("Connections", back_populates="user",
                               foreign_keys=[Connections.user_id], cascade="all, delete, delete-orphan")
    connected_to = relationship("Connections", back_populates="connected_user",
                                foreign_keys=[Connections.connected_user_id], cascade="all, delete, delete-orphan")

    def __init__(self, *args, **kwargs):
        """initializes user"""
        super().__init__(*args, **kwargs)

    def __setattr__(self, name, value):
        """sets a password with md5 encryption"""
        if name == "password":
            value = md5(value.encode()).hexdigest().lower()
        super().__setattr__(name, value)

    def check_password(self, password):
        """ Validate a password
        """
        return md5(password.encode()).hexdigest().lower() == self.password

        # return self.password == password


class Profile(BaseModel, Base):
    """Data model for User profile."""

    __tablename__ = "profiles"

    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="profile")
    about_me = Column(String(50), nullable=True)

    def __init__(self, *args, **kwargs):
        """initializes profile"""
        super().__init__(*args, **kwargs)


class Task(BaseModel, Base):
    """Data model for user tasks."""

    __tablename__ = "tasks"

    user_id = Column(ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    task_name = Column(String(255), name='task_name')
    subtasks = relationship("Subtask", cascade="all, delete, delete-orphan")
    assigned_users = relationship('User', secondary='assigned_tasks', back_populates='assigned_tasks')
    Column(String(2), default=lambda: datetime.utcnow().strftime("%m"))

    def __init__(self, *args, **kwargs):
        """initializes Task"""
        super().__init__(*args, **kwargs)
        self.month = self.created_at.strftime("%m")


class AssignedTasks(BaseModel, Base):
    __tablename__ = 'assigned_tasks'
    user_id = Column(String(60), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    task_id = Column(String(60), ForeignKey('tasks.id', ondelete="CASCADE"), primary_key=True)
    subtask_id = Column(String(60), ForeignKey('subtasks.id', ondelete="CASCADE"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        """initializes assigned tasks"""
        super().__init__(*args, **kwargs)

    @property
    def assigned_tasks(self):
        """getter for list of assigned tasks related to task"""
        assigned_tasks_list = []
        all_tasks = db.query(Task).all()
        for task in all_tasks.values():
            if task.id == self.task_id:
                assigned_tasks_list.append(task)
        return assigned_tasks_list

    @property
    def assigned_subtasks(self):
        """getter for list of subtasks related to task"""
        assigned_subtasks_list = []
        all_subtasks = db.query(Subtask).all()
        for sub in all_subtasks.values():
            if sub.id == self.subtask_id:
                assigned_subtasks_list.append(sub)
        return assigned_subtasks_list


class Subtask(BaseModel, Base):
    """Data model for user tasks."""

    __tablename__ = "subtasks"

    due_date = Column(DateTime)
    task = relationship("Task", back_populates="subtasks")
    title = Column(String(255), nullable=False)
    task_id = Column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(60), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(String(64), ForeignKey("users.username", ondelete="CASCADE"))
    content = Column(String(255), nullable=True)
    status = Column(Enum('unassigned', 'assigned', 'started',
                         'in-progress', 'done', 'null', name='tasks_status'),
                    server_default='unassigned')

    def __init__(self, *args, **kwargs):
        """initializes subtasks"""
        super().__init__(*args, **kwargs)

    @property
    def subtasks(self):
        """getter for list of subtasks related to task"""
        subtasks_list = []
        all_tasks = db.query(Task).all()
        for sub in all_tasks.values():
            if sub.id == self.task_id:
                subtasks_list.append(sub)
        return subtasks_list
