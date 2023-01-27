from flask import request, jsonify
from database import SessionLocal
from models import User, Profile
from flask_api import status
from flask_jwt_extended import jwt_required
import json

db = SessionLocal()


# CREATE READ, UPDATE, DELETE


# @jwt_required()
def update_profile():
    """	    It updates the user profile object
        :return: A response object
    """

    username = request.form["username"]
    about_me = request.form["about_me"]

    user = db.query(User).filter(User.username == username).first()
    get_user_profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    # return get_user_profile
    if not get_user_profile:
        return {"message": "Profile doesnt exist."}, status.HTTP_400_BAD_REQUEST

    # gets user
    user_account = db.query(User).filter(
        User.username == username).first()

    get_user_profile.about_me = about_me

    db.add(get_user_profile)
    db.commit()

    db.refresh(get_user_profile)
    user_account.profile = get_user_profile
    db.add(user_account)
    db.commit()

    return jsonify(my_profile=get_user_profile.to_dict()), 200


# @jwt_required()
def get_profile(username):
    user = db.query(User).filter(User.username == username).first()
    get_user_profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    if not get_user_profile:
        return {"message": "Profile doesnt exist."}, status.HTTP_400_BAD_REQUEST
    return get_user_profile.to_dict(), 200


@jwt_required()
def delete_profile(username):  # username

    user_account = db.query(User).filter(User.username == username).first()
    if user_account:
        get_profile_obj = db.query(Profile).filter(Profile.user_id == user_account.id).first()

        if not get_profile_obj:
            return {"message": "Profile doesnt exist."}, status.HTTP_400_BAD_REQUEST

        db.delete(get_profile_obj)
        db.commit()

        # also deletes user account.profile
        del user_account.profile
        db.commit()
        return {"message": "Profile has been successfully deleted"}

    return {"message": f"Account with username {username} does not exist."}, \
        status.HTTP_400_BAD_REQUEST


