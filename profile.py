from flask import request, jsonify
from database import SessionLocal
from models import User, Profile
from flask_api import status
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

db = SessionLocal()


# CREATE READ, UPDATE, DELETE


@jwt_required()
def update_profile():
    """	    It updates the user profile object
        :return: A response object
    """
    try:
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
    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


@jwt_required()
def get_profile(username):
    """	    It gets the user profile object
            :return: A response object
        """
    try:
        user = db.query(User).filter(User.username == username).first()
        get_user_profile = db.query(Profile).filter(Profile.user_id == user.id).first()

        if not get_user_profile:
            return {"message": "Profile doesnt exist."}, status.HTTP_400_BAD_REQUEST
        return get_user_profile.to_dict(), 200
    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


@jwt_required()
def delete_profile(username):
    """	    It deletes the user profile object
            :return: A response object
        """
    try:
        user_account = db.query(User).filter(User.username == username).first()
        if user_account:
            get_profile_obj = db.query(Profile).filter(Profile.user_id == user_account.id).first()

            if get_profile_obj:
                db.delete(get_profile_obj)
                db.commit()

                # also deletes user account.profile
                del user_account.profile
                db.commit()
                return {"message": "Profile has been successfully deleted"}
            return jsonify(message=f'Profile with username {username} does not exist.'), status.HTTP_400_BAD_REQUEST

        return jsonify(message=f"Account with username {username} does not exist."), status.HTTP_400_BAD_REQUEST

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST
