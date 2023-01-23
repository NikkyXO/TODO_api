from datetime import datetime
from flask import request, jsonify
from database import SessionLocal
from models import User, Profile
from flask_api import status
from flask_jwt_extended import (
    create_access_token, jwt_required, set_access_cookies,
    get_jwt, unset_jwt_cookies, verify_jwt_in_request, current_user
)

db = SessionLocal()


# CREATE READ, UPDATE, DELETE


# @jwt_required()
def update_profile():
    """
	It creates additional field to  user object
	:param user_data: This is the data that is passed to the function
	:return: A response object
	"""
    user_data = request.get_json()

    get_profile = db.query(Profile).filter(Profile.username == user_data["username"]).first()
    # return get_profile
    if not get_profile:
        content = {"message": "Profile doesnt exist."}
        return content, status.HTTP_400_BAD_REQUEST

    # gets user
    user_account = db.query(User).filter(
        User.username == user_data.get("username")).first()

    user_profile = Profile(
        about_me=user_data.get("about_me"),
        user_id=user_account.id,
        username="nike2"
    )
    db.add(user_profile)
    db.commit()
    db.refresh(user_profile)

    return jsonify(user_profile.to_dict()), 200


@jwt_required()
def get_profile(username):  # username
    get_profile = db.query(Profile).filter(
        Profile.username == username).first()

    if not get_profile:
        content = {"message": "Profile doesnt exist."}
        return content, status.HTTP_400_BAD_REQUEST
    return get_profile.to_dict(), 200


@jwt_required()
def delete_profile():  # username

    user_data = request.get_json()
    user_account = db.query(User).filter(
        User.username == user_data.get("username")).first()
    if user_account:
        get_profile_obj = db.query(Profile).filter(Profile.user_id == user_account.id).first()

        if not get_profile_obj:
            return {"message": "Profile doesnt exist."}, status.HTTP_400_BAD_REQUEST

        db.delete(get_profile_obj)
        db.commit()

        # also deletes user account
        db.delete(user_account)
        db.commit()
        return {"message": "Account and profile has been successfully deleted"}

    return {"message": f"Account with username {user_data} does not exist."}, \
        status.HTTP_400_BAD_REQUEST


@jwt_required()
def assign_to_profile():
    pass
