from flask import request, jsonify
from settings.database import SessionLocal
from .models import User, Profile
from flask_api import status
from sqlalchemy.exc import IntegrityError

db = SessionLocal()


# CREATE READ, UPDATE, DELETE

# create_profile if not exists endpoint

def update_profile():
    """	It updates the user profile object
        :return: A response object
    """
    try:
        username = request.form["username"]
        about_me = request.form["about_me"]

        get_user = db.query(User).filter(User.username == username).first()
        get_user_profile = db.query(Profile).filter(Profile.user_id == get_user.id).first()

        if not get_user_profile or not get_user:
            return {"message": "User or Profile doesnt exist."}, status.HTTP_400_BAD_REQUEST

        get_user_profile.about_me = about_me

        db.add(get_user_profile)
        db.commit()

        db.refresh(get_user_profile)
        get_user.profile = get_user_profile
        db.add(get_user)
        db.commit()

        db.refresh(get_user_profile)

        return jsonify(my_profile=get_user_profile.to_dict()), 200
    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def get_profile(username):
    """	It gets the user profile object
        :param username: The name of the user
        :return: A response object
    """
    try:
        get_user = db.query(User).filter(User.username == username).first()
        get_user_profile = db.query(Profile).filter(Profile.user_id == get_user.id).first()

        if not get_user_profile:
            return {"message": "Profile doesnt exist."}, status.HTTP_400_BAD_REQUEST
        return jsonify(message=get_user_profile.to_dict()), status.HTTP_200_OK
    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST


def delete_profile(username):
    """	It deletes the user profile object
        :param username: The name of the user
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
            return jsonify(message=f'User Profile does not exist.'), status.HTTP_400_BAD_REQUEST

        return jsonify(message=f"User Account does not exist."), status.HTTP_400_BAD_REQUEST

    except IntegrityError as e:
        db.rollback()
        return jsonify(message=str(e)), status.HTTP_400_BAD_REQUEST
