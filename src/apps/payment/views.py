from Crypto.Hash import SHA1
from sanic import Sanic
from sanic.response import json, empty
from sanic_ext import validate
from sqlalchemy import select

from apps.dimatech.models import CustomerBillModel
from apps.dimatech.validators import TransactionValidator
from apps.dimatech.views import TransactionAPI


@validate(json=TransactionValidator)
async def transaction_webhook(request, *args, **kwargs):
    """
    Webhook processes transactions from an external service.
    Checks the integrity of the data by signature, creates a new customer bill if it does not exist.

    Args:
        request: {
            signature: str
            transaction_id: int
            user_id: int
            bill_id: int
            amount: float = Field(ge=0.0)
        }
        *args: None
        **kwargs: None

    Returns: the transaction status.
    """
    sign_data = f"{Sanic.get_app().config.SIGNING_KEY}:{request.json.get('transaction_id')}:" \
                f"{request.json.get('user_id')}:{request.json.get('bill_id')}:{request.json.get('amount')}"
    signature = SHA1.new()
    signature.update(sign_data.encode())
    signature = signature.hexdigest()

    if signature != request.json.pop('signature'):
        return json({'status': 400, 'message': 'Wrong data'}, status=400)

    session = request.ctx.session
    async with session.begin():
        bill = await session.execute(
            select(CustomerBillModel).where(CustomerBillModel.id == int(request.json.get('bill_id'))))
        if not bill.first():
            obj = CustomerBillModel(user_id=request.json.get('user_id'))
            session.add(obj)

    request.json.pop('transaction_id')

    await TransactionAPI().post(request)
    return empty(status=201)
