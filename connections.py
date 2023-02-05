from flask import request
from database import SessionLocal
from models import User, Connections
from sqlalchemy.exc import IntegrityError
from flask_api import status
from flask_jwt_extended import (
    jwt_required, get_jwt_identity
)
from flask import jsonify


db = SessionLocal()


# review this
@jwt_required()
def add_connection(username, to_add, c_type):
    try:
        user = db.query(User).filter(User.username == username).first()
        user_to_be_connected = db.query(User).filter(User.username == to_add).first()
        if user and user_to_be_connected:
            new_connection = Connections(user_id=user.id,
                                         connection_type=c_type,
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

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


@jwt_required()
def remove_connected_user(username, to_remove):
    try:
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

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


@jwt_required()
def get_connected_users(username):
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return jsonify(message="Account not found ")

        connected_users = user.connections

        return jsonify(connected_users=connected_users), status.HTTP_201_CREATED
    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST
