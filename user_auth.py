import json
from flask import request
import datetime
from database import SessionLocal
from os import environ
from models import User, Profile
from flask import jsonify
from flask_api import status
from flask_jwt_extended import (
    create_access_token, jwt_required, set_access_cookies,
    get_jwt, unset_jwt_cookies, verify_jwt_in_request, current_user,
    get_jti, get_jwt_identity
)
from flask import Blueprint, jsonify
from flasgger import swag_from
from jwt_manager import jwt

db = SessionLocal()


@jwt_required()
def bearer_info_func(jwt):
    """
    Function that takes the request context
     and extracts the bearer token from it
    """
    user_id = get_jwt_identity()
    return db.query(User).filter(User.id == user_id).first()


def register():
    """
    It creates a new user
    :param : The request object
    :return: A response object
    """

    input_data = request.get_json()
    check_username_exist = db.query(User).filter(
        User.username == input_data.get("username")
    ).first()
    check_email_exist = db.query(User).filter(User.email == input_data.get("email")).first()
    if check_username_exist:
        content = {"message": "Username already exist"}
        return content, status.HTTP_400_BAD_REQUEST

    elif check_email_exist:
        content = {"message": "Email  already taken"}
        return content, status.HTTP_400_BAD_REQUEST

    new_user = User(email=input_data["email"],
                    username=input_data["username"], password=input_data["password"])
    new_user.hash_password()
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Instantites a new profile object here
    profile_obj = Profile(
        user_id=new_user.id,
        username=new_user.username)

    db.add(profile_obj)
    db.commit()

    content = {"message": "User Created."}
    return content, status.HTTP_201_CREATED


def login():
    """
    It takes in a request and input data, validates the input data
    the password is correct, and returns an an access token
    :param input_data: The data that is passed to the function
    :return: A dictionary with the keys: access token,  message, status
    """
    input_data = request.get_json()
    get_user = db.query(User).filter(User.username == input_data.get("username")).first()
    if not get_user:
        content = {"message": "User not found."}
        return content, status.HTTP_400_BAD_REQUEST

    if get_user.check_password(input_data.get("password")):
        access_token = create_access_token(identity=get_user.id)
        return jsonify(access_token=access_token)

    else:
        content = {"message": "Invalid credentials."}
        return content, status.HTTP_400_BAD_REQUEST


# utils
@jwt_required()
def protected_api():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


# JWT ID (JTI) is a unique identifier for a JSON Web Token (JWT)
#  that is used to prevent token replay attacks
@jwt_required()
def logout():
    jti = get_jwt_identity()
    jwt.revoke_token(jti)
    return jsonify({"msg": "Successfully logged out"}), 200

# to implement : delete account

# @jwt_required()
# def delete_account(user_data): #username, email
#     user_account = db.query(User).filter(User.email=user_data.get("email"),
#        User.username=user_data.get("username").first()

#     if not user_account :
#         content = {"message": "Account doesnt exist."}
#         return content, status.HTTP_400_BAD_REQUEST

#     db.delete(user_account)
#     db.commit()


