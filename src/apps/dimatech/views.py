from sanic import Request, response
from sanic.response import json, empty
from sanic.views import HTTPMethodView
from sanic_ext import validate
from sanic_jwt_extended import jwt_required
from sqlalchemy import select, update, delete

from apps.auth.models import User
from apps.dimatech.models import BaseModel, ProductModel, CustomerBillModel, TransactionModel, PurchaseModel
from apps.dimatech.validators import ProductValidator, CustomerBillValidator, TransactionValidator, PurchaseValidator

from decimal import Decimal


class BaseAPI(HTTPMethodView):
    def __init__(self):
        self.model = BaseModel
        self.query = None

    async def get(self, request: Request, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            if kwargs['token'].role == 'Admin':
                return await session.execute(self.query)
            else:
                return await session.execute(self.query.where(User.username == kwargs['token'].identity))

    async def post(self, request: Request, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            product = self.model(**request.json)
            session.add(product)
        return json(request.json, status=201)


class BaseDetailAPI(HTTPMethodView):
    def __init__(self):
        self.model = BaseModel
        self.query = None

    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        return empty()

    @jwt_required(allow=['Admin'])
    @validate(json=ProductValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session

        async with session.begin():
            data = await session.execute(select(self.model).where(self.model.id == pk))
            if data.scalar_one_or_none():
                await session.execute(update(self.model).values(**request.json).where(self.model.id == pk))
                return json(request.json, status=200)
            else:
                data = self.model(**request.json)
                session.add(data)
                return json(request.json, status=201)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session

        async with session.begin():
            await session.execute(update(self.model).values(**request.json).where(self.model.id == pk))
        return json(request.json, status=200)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            await session.execute(delete(self.model).where(self.model.id == pk))
        return empty(status=200)


class ProductAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.model = ProductModel

    async def get(self, request: Request, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            products = await session.execute(select(ProductModel).order_by(ProductModel.id))
        products = products.scalars().all()
        products = {
            'products': [{'title': product.title, 'description': product.description, 'price': product.price} for
                         product in products]}
        return json(products)

    @jwt_required(allow=['Admin'])
    @validate(json=ProductValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        return await super(ProductAPI, self).post(request, *args, **kwargs)


class ProductDetailAPI(BaseDetailAPI):
    def __init__(self):
        super().__init__()
        self.model = ProductModel

    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            product = await session.execute(select(ProductModel).where(ProductModel.id == pk))
        product = product.scalars().first()
        if not product:
            return json({'status': 400, 'msg': 'Record does not exist'}, status=400)
        product = {'id': product.id, 'title': product.title, 'description': product.description, 'price': product.price}
        return json(product)

    @jwt_required(allow=['Admin'])
    @validate(json=ProductValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(ProductDetailAPI, self).put(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(ProductDetailAPI, self).patch(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(ProductDetailAPI, self).delete(request, *args, **kwargs)


class CustomerBillAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.model = CustomerBillModel

    @jwt_required
    async def get(self, request: Request, *args, **kwargs) -> response:
        self.query = select(CustomerBillModel, User.username).join(User, User.id == CustomerBillModel.user_id)
        bills = await super(CustomerBillAPI, self).get(request, *args, **kwargs)
        bills = bills.all()
        bills = {'bills': [{'id': bill.id, 'user_id': bill.user_id, "username": username, 'balance': bill.balance} for
                           bill, username in bills]}
        return json(bills)

    @jwt_required
    @validate(json=CustomerBillValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        return await super(CustomerBillAPI, self).post(request, *args, **kwargs)


class CustomerBillDetailAPI(BaseDetailAPI):
    def __init__(self):
        super().__init__()
        self.model = CustomerBillModel

    @jwt_required
    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            bill = await session.execute(
                select(CustomerBillModel, User.username).join(User, User.id == CustomerBillModel.user_id).where(
                    CustomerBillModel.id == pk))
        if not bill:
            return json({'status': 404, 'msg': 'Record does not exist'}, status=404)
        bill, username = bill.first()
        if (kwargs['token'].role == 'Admin') or (username == kwargs['token'].identity):
            bill = {'id': bill.id, 'user_id': bill.user_id, "username": username, 'balance': bill.balance}
            return json(bill)
        else:
            return empty(status=403)

    @jwt_required(allow=['Admin'])
    @validate(json=CustomerBillValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(CustomerBillDetailAPI, self).put(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(CustomerBillDetailAPI, self).patch(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(CustomerBillDetailAPI, self).delete(request, *args, **kwargs)


class TransactionAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.model = TransactionModel

    @jwt_required
    async def get(self, request: Request, *args, **kwargs) -> response:
        self.query = select(TransactionModel, User.username).join(User, User.id == TransactionModel.user_id)
        transactions = await super(TransactionAPI, self).get(request, *args, **kwargs)
        transactions = transactions.all()
        transactions = {'transactions': [
            {'transaction': transaction.id, 'user_id': transaction.user_id, "username": username,
             'bill_id': transaction.bill_id, 'amount': transaction.amount} for transaction, username in transactions]}
        return json(transactions)

    @jwt_required(allow=['Admin'])
    @validate(json=TransactionValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            bill = await session.execute(
                select(CustomerBillModel).where(CustomerBillModel.id == request.json.get('bill_id')))
            bill = bill.scalars().first()
            await session.execute(
                update(CustomerBillModel).values({'balance': bill.balance + Decimal(request.json.get('amount'))}).where(
                    CustomerBillModel.id == request.json.get('bill_id')))
        return await super(TransactionAPI, self).post(request, *args, **kwargs)


class TransactionDetailAPI(BaseDetailAPI):
    def __init__(self):
        super().__init__()
        self.model = TransactionModel

    @jwt_required
    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            transaction = await session.execute(
                select(TransactionModel, User.username).join(User, User.id == TransactionModel.user_id).where(
                    TransactionModel.id == pk))
        if not transaction:
            return json({'status': 404, 'msg': 'Record does not exist'}, status=404)
        transaction, username = transaction.first()
        if (kwargs['token'].role == 'Admin') or (username == kwargs['token'].identity):
            transaction = {'transaction': transaction.id, 'user_id': transaction.user_id, "username": username,
                           'bill_id': transaction.bill_id, 'amount': transaction.amount}
            return json(transaction)
        else:
            return empty(status=403)

    @jwt_required(allow=['Admin'])
    @validate(json=TransactionValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(TransactionDetailAPI, self).put(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(TransactionDetailAPI, self).patch(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(TransactionDetailAPI, self).delete(request, *args, **kwargs)


class PurchaseAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.model = PurchaseModel

    @jwt_required
    async def get(self, request: Request, *args, **kwargs) -> response:
        self.query = select(PurchaseModel, ProductModel.title, User.username).\
            join(ProductModel, ProductModel.id == PurchaseModel.product_id).\
            join(User, User.id == PurchaseModel.user_id)
        purchases = await super(PurchaseAPI, self).get(request, *args, **kwargs)
        purchases = purchases.all()
        purchases = {'purchases': [
            {'id': purchase.id, 'product_id': purchase.product_id, 'title': title,
             'user_id': purchase.user_id, "username": username,  'bill_id': purchase.bill_id}
            for purchase, title, username in purchases]}
        return json(purchases)

    @jwt_required
    @validate(json=PurchaseValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            bill = await session.execute(
                select(CustomerBillModel).where(CustomerBillModel.id == request.json.get('bill_id')))
            bill = bill.scalars().first()

            product = await session.execute(
                select(ProductModel).where(ProductModel.id == request.json.get('product_id')))
            product = product.scalars().first()

            await session.execute(update(CustomerBillModel).values({'balance': bill.balance - product.price}).where(
                CustomerBillModel.id == request.json.get('bill_id')))
        return await super(PurchaseAPI, self).post(request, *args, **kwargs)


class PurchaseDetailAPI(BaseDetailAPI):
    def __init__(self):
        super().__init__()
        self.model = PurchaseModel

    @jwt_required
    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            if kwargs['token'].role == 'Admin':
                purchase = await session.execute(
                    select(PurchaseModel, ProductModel.title, User.username).
                    join(ProductModel, User, ProductModel.id == PurchaseModel.product_id,
                         User.id == PurchaseModel.user_id).where(PurchaseModel.id == pk))
            else:
                purchase = await session.execute(
                    select(PurchaseModel, ProductModel.title, User.username).
                    join(ProductModel, User, ProductModel.id == PurchaseModel.product_id,
                         User.id == PurchaseModel.user_id).
                    where(PurchaseModel.id == pk, User.username == kwargs['token'].identity))
        if not purchase:
            return json({'status': 404, 'msg': 'Record does not exist'}, status=404)
        purchase, username = purchase.first()
        if (kwargs['token'].role == 'Admin') or (username == kwargs['token'].identity):
            purchase = {'id': purchase.id, 'user_id': purchase.user_id, "username": username,
                        'product_id': purchase.product_id, 'title': purchase.title, 'bill_id': purchase.bill_id}
            return json(purchase)
        else:
            return empty(status=403)

    @jwt_required(allow=['Admin'])
    @validate(json=PurchaseValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(PurchaseDetailAPI, self).put(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(PurchaseDetailAPI, self).patch(request, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        return await super(PurchaseDetailAPI, self).delete(request, *args, **kwargs)
