from database import SessionLocal
from models import User, Profile
from sqlalchemy.exc import IntegrityError
from flask_api import status
from flask_jwt_extended import (
    create_access_token, jwt_required
)
from flask import jsonify, request

db = SessionLocal()


def register():
    """
    It creates a new user
    :return: A response object
    """
    try:
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        check_username_exist = db.query(User).filter(
            User.username == username).first()
        check_email_exist = db.query(User).filter(User.email == email).first()

        if check_username_exist:
            return {"message": f"Account with username {username} already exist"}, status.HTTP_400_BAD_REQUEST

        if check_email_exist:
            return {"message": "Email  already taken"}, status.HTTP_400_BAD_REQUEST

        new_user = User(username=username, email=email, password=password)
        new_user.hash_password()
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Instantiates a new profile object here
        profile_obj = Profile(
            user_id=new_user.id,
            user=new_user)

        db.add(profile_obj)
        db.commit()
        return {"message": "User Created Successfully."}, status.HTTP_201_CREATED

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def login():
    """
    It takes in a request and input data, validates the input data
    the password is correct, and returns  an access token
    :request body input_data: The data that is passed to the function
    :return: A dictionary with the keys: access token,  message, status
    """
    username = request.form["username"]
    password = request.form["password"]
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
# def logout():
#     """
#         It logs out a user
#         :return: A response object
#     """
#     jti = get_jwt_identity()
#     jwt.revoke_token(jti)
#     return jsonify({"msg": "Successfully logged out"}), 200

# to implement : delete account

@jwt_required()
def delete_account(email, username):
    """
        It takes parameters and deletes a user account
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
