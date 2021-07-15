import traceback
from time import time

from flask import make_response, render_template
from flask_restful import Resource

from libs.mailgun import MailGunException
from models.confirmation import ConfirmationModel
from models.user import UserModel
from schemas.confirmation import ConfirmationSchema
from libs.strings import get_text

confirmation_schema = ConfirmationSchema()


class Confirmation(Resource):
    @classmethod
    def get(cls, confirmation_id: str):
        confirmation = ConfirmationModel.find_by_id(confirmation_id)

        if not confirmation:
            return {"message": get_text("confirmation_not_found")}, 404

        if confirmation.expired():
            return {"message": get_text("confirmation_expired")}, 400

        if confirmation.confirmed:
            return {"message": get_text("confirmation_already_confirmed")}, 400

        confirmation.confirmed = True
        confirmation.save_to_db()

        email = UserModel.find_by_id(confirmation.user_id).email
        headers = {"Content-Type": "text/html"}
        return make_response(
            render_template("confirmation_page.html", email=email),
            200,
            headers
        )


class ConfirmationByUser(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": get_text("confirmation_user_not_found")}, 404

        return ({
                    "current_time": int(time()),
                    "confirmation": [
                        confirmation_schema.dump(each)
                        for each in user.confirmation.order_by(ConfirmationModel.expire_at)
                    ]
                }, 200)

    @classmethod
    def post(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": get_text("confirmation_user_not_found")}, 404

        try:
            confirmation = user.most_recent_confirmation
            if confirmation:
                if confirmation.confirmed:
                    return {"message": get_text("confirmation_already_confirmed")}, 400

                confirmation.force_to_expire()

            new_confirmation = ConfirmationModel(user_id)
            new_confirmation.save_to_db()
            user.send_confirmation_email()
            return {"message": get_text("confirmation_resend_successful")}, 201
        except MailGunException as e:
            return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            return {"message": get_text("confirmation_resend_fail")}, 500
