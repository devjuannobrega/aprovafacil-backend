import mercadopago
from src.core.config import settings
from src.schemas.payment import PaymentRequest, PreferenceRequest


class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    def get_public_key(self) -> str:
        return settings.MP_PUBLIC_KEY

    def create_payment(self, payment: PaymentRequest) -> dict:
        payment_data = {
            "token": payment.token,
            "transaction_amount": payment.transaction_amount,
            "installments": payment.installments,
            "payment_method_id": payment.payment_method_id,
            "payer": {
                "email": payment.payer.email,
            }
        }

        if payment.issuer_id:
            payment_data["issuer_id"] = payment.issuer_id

        if payment.payer.first_name:
            payment_data["payer"]["first_name"] = payment.payer.first_name

        if payment.payer.last_name:
            payment_data["payer"]["last_name"] = payment.payer.last_name

        if payment.payer.identification:
            payment_data["payer"]["identification"] = {
                "type": payment.payer.identification.type,
                "number": payment.payer.identification.number
            }

        if payment.description:
            payment_data["description"] = payment.description

        if payment.external_reference:
            payment_data["external_reference"] = payment.external_reference

        return self.sdk.payment().create(payment_data)

    def create_preference(self, preference: PreferenceRequest) -> dict:
        preference_data = {
            "items": [
                {
                    "title": item.title,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "currency_id": item.currency_id,
                }
                for item in preference.items
            ]
        }

        for i, item in enumerate(preference.items):
            if item.id:
                preference_data["items"][i]["id"] = item.id
            if item.description:
                preference_data["items"][i]["description"] = item.description

        if preference.payer:
            preference_data["payer"] = {"email": preference.payer.email}
            if preference.payer.first_name:
                preference_data["payer"]["first_name"] = preference.payer.first_name
            if preference.payer.last_name:
                preference_data["payer"]["last_name"] = preference.payer.last_name

        if preference.external_reference:
            preference_data["external_reference"] = preference.external_reference

        if preference.notification_url:
            preference_data["notification_url"] = preference.notification_url

        return self.sdk.preference().create(preference_data)

    def get_payment(self, payment_id: str) -> dict:
        return self.sdk.payment().get(payment_id)

    def get_payment_methods(self) -> dict:
        return self.sdk.payment_methods().list_all()

    def get_installments(self, amount: float, bin: str) -> dict:
        return self.sdk.installments().get({
            "amount": amount,
            "bin": bin
        })


def get_mercadopago_service() -> MercadoPagoService:
    return MercadoPagoService()
