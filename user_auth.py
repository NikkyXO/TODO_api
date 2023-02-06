from database import SessionLocal
from models import User, Profile
from sqlalchemy.exc import IntegrityError
from flask_api import status
from flask_jwt_extended import (
    create_access_token, jwt_required
)
from flask import jsonify, request, abort

db = SessionLocal()


def register():
    """ It creates a new user
    :return: A response object
    """

    input_data = None
    error_msg = None
    try:
        input_data = request.form
    except Exception as e:
        input_data = None

    if input_data is None:
        error_msg = "Wrong format"

    if error_msg is None and input_data.get("username"):
        check_username_exist = db.query(User).filter(
            User.username == input_data.get("username")).first()

        if check_username_exist:
            error_msg = "username already exists"

    if error_msg is None and input_data.get("email"):
        check_email_exist = db.query(User).filter(User.email == input_data.get("email")).first()

        if check_email_exist:
            error_msg = "email already exists"

    if error_msg is None:
        try:
            user = User()
            user.email = input_data.get("email")
            user.password = input_data.get("password")
            user.username = input_data.get("username")

            # user.save()
            db.add(user)
            db.commit()
            db.refresh(user)

            # Instantiates a new profile object here
            user_profile = Profile()
            user_profile.user_id = user.id
            user_profile.user = user
            db.add(user_profile)
            db.commit()

            db.refresh(user)

            return jsonify(user.to_json()), status.HTTP_201_CREATED
        except Exception as e:
            error_msg = "Can't create User: {}".format(e)
    return jsonify({'error': error_msg}), status.HTTP_400_BAD_REQUEST


def login():
    """ It takes in a request and input data, validates the input data
    the password is correct, and returns  an access token
    :request body input_data: The data that is passed to the function
    :return: A dictionary with the keys: access token,  message, status
    """

    input_data = request.form
    username = input_data.get("username")
    password = input_data.get("password")

    try:
        get_user = db.query(User).filter(User.username == username).first()
        if not get_user:
            return {"message": "User not found."}, status.HTTP_400_BAD_REQUEST

        if get_user.check_password(password):
            access_token = create_access_token(identity=get_user.id)
            return jsonify(access_token=access_token)

        else:
            return {"message": "Invalid credentials."}, status.HTTP_400_BAD_REQUEST

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


@jwt_required()
def delete_account(email, username):
    """ It takes parameters and deletes a user account
        :param email: The email of the user
        :param username: The name of the user
        :return: A Response Object.
    """
    try:
        user_account = db.query(User).filter(User.email == email,
                                             User.username == username).first()

        if not user_account:
            content = {"message": "Account doesnt exist."}
            return content, status.HTTP_400_BAD_REQUEST

        db.delete(user_account)
        db.commit()

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST
