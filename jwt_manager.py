from flask_jwt_extended import JWTManager, decode_token

jwt = JWTManager()


# print(f"user_id---->{user_id}") print(f"user---->{user}")

# def decode_token_fxn(token):
# 	decoded_token =
# 	user_id = decoded_token.get("sub")
# 	user = User.get_by_id(user_id)
# 	return user

def security_handler(token):
    return decode_token(token)
# user =
# if user:
# 	return True
# request.context['user'] = user.get_id()
# return user
