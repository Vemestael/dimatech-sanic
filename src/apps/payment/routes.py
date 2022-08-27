from sanic import Blueprint

import apps.payment.views as views

blueprint = Blueprint('payment_app', url_prefix='/payment', version=1)

blueprint.add_route(views.transaction_webhook, '/webhook', methods=['POST'])
