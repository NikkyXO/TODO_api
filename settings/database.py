from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask import Flask
import os

app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://root:410208olA$$$@localhost/todoApp_db"

# SQLALCHEMY_DATABASE_URI =
# "mysql+mysqldb://olapeju:410208olA$@olapeju.mysql.pythonanywhere-services.com/olapeju$default"

engine = create_engine(SQLALCHEMY_DATABASE_URI)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
