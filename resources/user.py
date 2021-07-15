import hmac
import traceback
from datetime import datetime
from datetime import timezone

from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from libs.mailgun import MailGunException
from schemas.user import UserSchema
from models.user import UserModel, TokenBlocklist
from models.confirmation import ConfirmationModel
from libs.strings import get_text

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user = user_schema.load(user_json)

        if UserModel.find_by_username(user.username):
            return {'message': get_text("user_already_exists")}, 400

        if UserModel.find_by_email(user.email):
            return {'message': get_text("user_email_already_exists")}, 400

        try:
            user.save_to_db()
            confirmation = ConfirmationModel(user.id)
            confirmation.save_to_db()
            user.send_confirmation_email()
            return {"message": get_text("user_created_successfully")}, 201
        except MailGunException as e:
            user.delete_from_db()
            return {"message", str(e)}, 500
        except:
            traceback.print_exc()
            user.delete_from_db()
            return {"message": get_text("user_failed_to_create")}, 500


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': get_text("user_not_found")}, 404

        return user_schema.dump(user), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': get_text("user_not_found")}, 404

        user.delete_from_db()
        return {'message': get_text("user_deleted")}, 200


class UserLogin(Resource):
    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json, partial=("email",))

        user = UserModel.find_by_username(user_data.username)

        if user and hmac.compare_digest(user.password, user_data.password):
            confirmation = user.most_recent_confirmation
            if confirmation and confirmation.confirmed:
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)
                return {
                           'access_token': access_token,
                           'refresh_token': refresh_token
                       }, 200
            return {'message:': get_text("user_not_confirmed_error").format(user.username)}, 400

        return {'message': get_text("user_invalid_credentials")}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required()
    def post(cls):
        jti = get_jwt()["jti"]
        now = datetime.now(timezone.utc)
        token_blocklist = TokenBlocklist(jti, now)
        token_blocklist.save_to_db()
        return {'message': get_text("user_logged_out")}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200
