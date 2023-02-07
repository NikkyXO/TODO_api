from flask import request
from settings.database import SessionLocal
from .models import User, Connections
from sqlalchemy.exc import IntegrityError
from flask_api import status
from flask import jsonify
from sqlalchemy import exc


db = SessionLocal()


def add_connection():
    """	 It adds the user connection to user account
        :return: A response object
    """

    username = request.form['username']
    to_add = request.form['to_add']
    c_type = request.form['c_type']
    try:
        get_user = db.query(User).filter(User.username == username).first()
        user_to_be_connected = db.query(User).filter(User.username == to_add).first()
        if get_user and user_to_be_connected:
            connected_before = db.query(Connections). \
                filter(Connections.connected_user_id == user_to_be_connected.id).first()

            if connected_before:
                return jsonify(message="Connection already exist"), status.HTTP_400_BAD_REQUEST

            new_connection = Connections(user_id=get_user.id,
                                         connected_user_id=user_to_be_connected.id,
                                         connection_type=c_type)
            new_connection.connected_name = user_to_be_connected.username
            db.add(new_connection)
            db.commit()
            get_user.connections.append(new_connection)
            db.commit()
            db.refresh(new_connection)
            return jsonify(message="Connection added",
                           new_connection=new_connection.to_dict()), status.HTTP_201_CREATED
        return jsonify(message="Account or user to create connection not found "), status.HTTP_404_NOT_FOUND

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def remove_connected_user(username, to_remove):  # REVISE
    """It removes the user connection from user account
         :param username: The name of the user
         :param to_remove: The name of the user to be removed from connections
        :return: A response object
    """
    try:
        user = db.query(User).filter(User.username == username).first()
        user_to_be_removed = db.query(User).filter(User.username == to_remove).first()

        if user and user_to_be_removed:
            be_removed = db.query(Connections) \
                .filter(Connections.user_id == user.id,
                        Connections.connected_user_id == user_to_be_removed.id).first()

            if not be_removed:
                return jsonify(message="Connection not found"), \
                    status.HTTP_404_NOT_FOUND

            db.delete(be_removed)
            db.commit()

            # review this
            if be_removed in user.connections:
                user.connections.remove(be_removed)
                db.commit()

            return jsonify(message="Connection removed successfully",
                           ), status.HTTP_202_ACCEPTED

        return jsonify(message="Account or user to remove connection not found"), status.HTTP_404_NOT_FOUND

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def get_connected_users(username):
    """	 It retrieves all the user connections
         :param username: The name of the user to be assigned subtask
        :return: A response object
    """
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return jsonify(message="Account not found ")

        connected_users = user.connections
        _connected_users = [user.to_dict() for user in connected_users]

        return jsonify(connected_users=_connected_users), status.HTTP_201_CREATED
    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def get_all_users():
    """	It retrieves all users from the database
        :return: A response object
    """

    try:
        # all_users = db.query(User.id, User.username, User.email).all()
        all_users = db.query(User).all()

        if not all_users:
            return jsonify(message="No user exists")
        users = [user.to_dict() for user in all_users]

        return jsonify(users=users)

    except exc.DatabaseError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST
