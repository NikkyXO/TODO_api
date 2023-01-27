from flask import request
from database import SessionLocal
from models import User, Profile, Connections
from flask import jsonify
from flask_api import status
from flask_jwt_extended import (
    jwt_required
)
from flask import jsonify
from jwt_manager import jwt

db = SessionLocal()


# review this
@jwt_required()
def add_connection(username, to_add, connection_type):
    user = db.query(User).filter(User.username == username).first()
    user_to_be_connected = db.query(User).filter(User.username == to_add).first()
    if user and user_to_be_connected:
        new_connection = Connections(user_id=user.id,
                                     connection_type=connection_type,
                                     connected_user=user_to_be_connected)

        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)

        user.connections.append(new_connection)
        db.add(user)
        db.commit()
        return jsonify(message="Connection added",
                       new_connection=new_connection.to_json()), status.HTTP_201_CREATED
    return jsonify(message="Account or user to create connection not found "), status.HTTP_404_NOT_FOUND


@jwt_required()
def remove_connected_user(username, to_remove):
    user = db.query(User).filter(User.username == username).first()
    user_to_be_removed = db.query(User).filter(User.username == to_remove).first()

    if user and user_to_be_removed:

        be_removed = db.query(Connections) \
            .filter(Connections.user_id == user.id,
                    Connections.connected_user == user_to_be_removed).first()

        db.delete(be_removed)
        db.commit()

        user.connections.remove(be_removed)
        db.add(user)
        db.commit()
        return jsonify(message="Connection removed successfully",
                       ), status.HTTP_202_ACCEPTED
    return jsonify(message="Account or user to remove connection not found"), status.HTTP_404_NOT_FOUND


def get_connected_users(username):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return jsonify(message="Account not found ")

    connected_users = user.connections

    return jsonify(connected_users=connected_users), status.HTTP_201_CREATED
