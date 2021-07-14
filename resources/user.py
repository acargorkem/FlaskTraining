import hmac
from datetime import datetime
from datetime import timezone

from flask_restful import Resource, reqparse
from models.user import UserModel, TokenBlocklist
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

BLANK_ERROR = "{} cannot be left blank."
USER_NOT_FOUND = "User not found"
USER_ALREADY_EXISTS = "A user with that username already exists."
CREATED_SUCCESSFULLY = "User created successfully."
ERROR_INSERTING = "An error occurred inserting the item."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials."
USER_LOGGED_OUT = "Successfully logged out."

_user_parser = reqparse.RequestParser()
_user_parser.add_argument('username', type=str, required=True, help=BLANK_ERROR.format("Username"))
_user_parser.add_argument('password', type=str, required=True, help=BLANK_ERROR.format("Password"))


class UserRegister(Resource):

    @classmethod
    def post(cls):
        data = _user_parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {'message': USER_ALREADY_EXISTS}, 400

        user = UserModel(**data)
        user.save_to_db()

        return {"message": CREATED_SUCCESSFULLY}, 201


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': USER_NOT_FOUND}, 404

        return user.json()

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': USER_NOT_FOUND}, 404

        user.delete_from_db()
        return {'message': USER_DELETED}, 200


class UserLogin(Resource):

    @classmethod
    def post(cls):
        data = _user_parser.parse_args()
        user = UserModel.find_by_username(data['username'])

        if user and hmac.compare_digest(user.password, data['password']):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return {
                       'access_token': access_token,
                       'refresh_token': refresh_token
                   }, 200

        return {'message': INVALID_CREDENTIALS}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required()
    def post(cls):
        jti = get_jwt()["jti"]
        now = datetime.now(timezone.utc)
        token_blocklist = TokenBlocklist(jti, now)
        token_blocklist.save_to_db()
        return {'message': USER_LOGGED_OUT}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200
