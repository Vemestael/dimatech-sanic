from decimal import Decimal

from apps.auth.models import User
from apps.dimatech.models import BaseModel, ProductModel, CustomerBillModel, TransactionModel, PurchaseModel
from apps.dimatech.validators import ProductValidator, CustomerBillValidator, TransactionValidator, PurchaseValidator
from sanic import Request, response
from sanic.response import json, empty
from sanic.views import HTTPMethodView
from sanic_ext import validate
from sanic_jwt_extended import jwt_required
from sqlalchemy import select, update, delete


class BaseAPI(HTTPMethodView):
    """
    The class provides a basic implementation of the GET and POST methods of the REST API
    """

    def __init__(self):
        self.model = BaseModel
        self.query = None

    async def get(self, request: Request, *args, **kwargs) -> response:
        """
        Returns the list of records of the specified model.
        For an administrator it returns all records, for a default user it returns records related to him.
        Args:
            request: None
            *args: None
            **kwargs: token: JWT access token
        """
        session = request.ctx.session
        async with session.begin():
            if kwargs['token'].role == 'Admin':
                return await session.execute(self.query)
            else:
                return await session.execute(self.query.where(User.username == kwargs['token'].identity))

    async def post(self, request: Request, *args, **kwargs) -> response:
        """
        Creates a new record for the specified model

        Returns: HTTP 201 Created and request body
        """
        session = request.ctx.session
        async with session.begin():
            obj = self.model(**request.json)
            session.add(obj)
        return json(request.json, status=201)


class BaseDetailAPI(HTTPMethodView):
    """
    The class provides a basic implementation of the GET, PUT, PATCH and DELETE methods for the REST API.
    """

    def __init__(self):
        self.model = BaseModel
        self.query = None

    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements template for the GET method for the REST API
        """
        return empty()

    @jwt_required(allow=['Admin'])
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements the PUT method for the REST API
        """
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
        """
        Implements the PATCH method for the REST API
        """
        session = request.ctx.session

        async with session.begin():
            await session.execute(update(self.model).values(**request.json).where(self.model.id == pk))
        return json(request.json, status=200)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements the DELETE method for the REST API
        """
        session = request.ctx.session
        async with session.begin():
            await session.execute(delete(self.model).where(self.model.id == pk))
        return empty(status=200)


class ProductAPI(BaseAPI):
    """
    REST API for getting the list of products and their creation
    """

    def __init__(self):
        super().__init__()
        self.model = ProductModel

    async def get(self, request: Request, *args, **kwargs) -> response:
        """
        Returns the list of records of products.
        Each record consists of:
        - product id;
        - title;
        - description;
        - price.
        """
        session = request.ctx.session
        async with session.begin():
            products = await session.execute(select(ProductModel).order_by(ProductModel.id))
        products = products.scalars().all()
        products = {
            'products': [{'id': product.id, 'title': product.title,
                          'description': product.description, 'price': product.price} for
                         product in products]}
        return json(products)

    @jwt_required(allow=['Admin'])
    @validate(json=ProductValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        """
        Implements POST method of REST API
        Requires JWT access token and administrator rights

        Args:
            request: {
                title: str = Field(max_length=50)
                description: Optional[str]
                price: float = Field(ge=0.0)
                }
            *args: None
            **kwargs: None

        Returns: HTTP 201 Created and request body
        """
        return await super(ProductAPI, self).post(request, *args, **kwargs)


class ProductDetailAPI(BaseDetailAPI):
    """
    REST API for getting detailed information on a product and editing it
    """

    def __init__(self):
        super().__init__()
        self.model = ProductModel

    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Returns detailed information about the product, namely:
        - product id;
        - title;
        - description;
        - price.
        """
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
        """
        Implements PUT method of REST API
        Requires JWT access token and administrator rights

        Args:
            pk: int
            request: {
                title: str = Field(max_length=50)
                description: Optional[str]
                price: float = Field(ge=0.0)
                }

        Returns: HTTP 200 OK | HTTP 201 Created
        """
        return await super(ProductDetailAPI, self).put(request, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements PATCH method of REST API
        Requires JWT access token and administrator rights

        Args:
            pk: int
            request: {
                title: Optional[str] = Field(max_length=50)
                description: Optional[str]
                price: Optional[float] = Field(ge=0.0)
                }

        Returns: HTTP 200 OK
        """
        return await super(ProductDetailAPI, self).patch(request, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements DELETE method of REST API
        Requires JWT access token and administrator rights
        """
        return await super(ProductDetailAPI, self).delete(request, pk, *args, **kwargs)


class CustomerBillAPI(BaseAPI):
    """
    REST API for getting the list of customer bills and their creation
    """

    def __init__(self):
        super().__init__()
        self.model = CustomerBillModel

    @jwt_required
    async def get(self, request: Request, *args, **kwargs) -> response:
        """
        Returns the list of records of the customer bills.
        Each record consists of:
        - bill id;
        - user_id;
        - username, which is taken from the associated User table;
        - balance.
        For an administrator it returns all records, for a default user it returns records related to him.
        """
        self.query = select(CustomerBillModel, User.username).join(User, User.id == CustomerBillModel.user_id)
        bills = await super(CustomerBillAPI, self).get(request, *args, **kwargs)
        bills = bills.all()
        bills = {'bills': [{'id': bill.id, 'user_id': bill.user_id, "username": username, 'balance': bill.balance} for
                           bill, username in bills]}
        return json(bills)

    @jwt_required
    @validate(json=CustomerBillValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        """
        Implements POST method of REST API
        Requires JWT access token and administrator rights

        Args:
            request: {
                user_id: int
                balance: float = Field(ge=0.0)
                }
            *args:
            **kwargs:

        Returns: HTTP 201 Created and request body
        """
        return await super(CustomerBillAPI, self).post(request, *args, **kwargs)


class CustomerBillDetailAPI(BaseDetailAPI):
    """
    REST API for getting detailed information on a customer bill and editing it
    """

    def __init__(self):
        super().__init__()
        self.model = CustomerBillModel

    @jwt_required
    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Returns detailed information about the customer bill, namely:
        - bill id;
        - user_id;
        - username, which is taken from the associated User table;
        - balance.
        If the user is not the administrator and the record is not associated with the user, it returns an access error.
        If the record does not exist returns a missing data error.
        """
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
        """
        Implements PUT method of REST API
        Requires JWT access token and administrator rights

        Args:
            pk: int
            request: {
                user_id: int
                balance: float = Field(ge=0.0)
                }

        Returns: HTTP 200 OK | HTTP 201 Created
        """
        return await super(CustomerBillDetailAPI, self).put(request, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements PATCH method of REST API
        Requires JWT access token and administrator rights

        Args:
            pk: int
            request: {
                user_id: Optional[int]
                balance: Optional[float] = Field(ge=0.0)
                }

        Returns: HTTP 200 OK
        """
        return await super(CustomerBillDetailAPI, self).patch(request, pk, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements DELETE method of REST API
        Requires JWT access token and administrator rights
        """
        return await super(CustomerBillDetailAPI, self).delete(request, pk, *args, **kwargs)


class TransactionAPI(BaseAPI):
    """
    REST API for getting the list of transactions and their creation
    """

    def __init__(self):
        super().__init__()
        self.model = TransactionModel

    @jwt_required
    async def get(self, request: Request, *args, **kwargs) -> response:
        """
        Returns the list of records of the transactions.
        Each record consists of:
        - transaction id;
        - user_id;
        - username, which is taken from the associated User table;
        - bill_id,
        - amount.
        For an administrator it returns all records, for a default user it returns records related to him.
        """
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
        """
        Implements POST method of REST API
        Requires JWT access token and administrator rights

        Changes the bill balance by the amount of the transaction
        Args:
            request: {
                user_id: int
                bill_id: int
                amount: float = Field(ge=0.0)
                }
            *args:
            **kwargs:

        Returns: HTTP 201 Created and request body
        """
        session = request.ctx.session
        async with session.begin():
            bill = await session.execute(
                select(CustomerBillModel).where(CustomerBillModel.id == request.json.get('bill_id')))
            bill = bill.scalars().first()
            await session.execute(update(CustomerBillModel).values(
                {'balance': Decimal(bill.balance) + Decimal(request.json.get('amount'))}).where(
                CustomerBillModel.id == request.json.get('bill_id')))
        return await super(TransactionAPI, self).post(request, *args, **kwargs)


class TransactionDetailAPI(BaseDetailAPI):
    """
    REST API for getting detailed information on a transaction and editing it
    """

    def __init__(self):
        super().__init__()
        self.model = TransactionModel

    @jwt_required
    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Returns detailed information about the transaction, namely:
        - transaction id;
        - user_id;
        - username, which is taken from the associated User table;
        - bill_id,
        - amount.
        If the user is not the administrator and the record is not associated with the user, it returns an access error.
        If the record does not exist returns a missing data error.
        """
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
        """
        Implements PUT method of REST API
        Requires JWT access token and administrator rights

        Args:
            pk: int
            request: {
                user_id: int
                bill_id: int
                amount: float = Field(ge=0.0)
                }

        Returns: HTTP 200 OK | HTTP 201 Created
        """
        return await super(TransactionDetailAPI, self).put(request, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements PATCH method of REST API
        Requires JWT access token and administrator rights

        Args:
            pk: int
            request: {
                user_id: Optional[int]
                bill_id: Optional[int]
                amount: Optional[float] = Field(ge=0.0)
                }

        Returns: HTTP 200 OK
        """
        return await super(TransactionDetailAPI, self).patch(request, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements DELETE method of REST API
        Requires JWT access token and administrator rights
        """
        return await super(TransactionDetailAPI, self).delete(request, pk, *args, **kwargs)


class PurchaseAPI(BaseAPI):
    """
    REST API for getting the list of purchases and their creation
    """

    def __init__(self):
        super().__init__()
        self.model = PurchaseModel

    @jwt_required
    async def get(self, request: Request, *args, **kwargs) -> response:
        """
        Returns the list of records of the purchases.
        Each record consists of:
        - purchase id;
        - product_id;
        - title, which is taken from the associated Product table;
        - user_id;
        - username, which is taken from the associated User table;
        - bill_id.
        For an administrator it returns all records, for a default user it returns records related to him.
        """
        self.query = select(PurchaseModel, ProductModel.title, User.username). \
            join(ProductModel, ProductModel.id == PurchaseModel.product_id). \
            join(User, User.id == PurchaseModel.user_id)
        purchases = await super(PurchaseAPI, self).get(request, *args, **kwargs)
        purchases = purchases.all()
        purchases = {'purchases': [
            {'id': purchase.id, 'product_id': purchase.product_id, 'title': title, 'user_id': purchase.user_id,
             "username": username, 'bill_id': purchase.bill_id} for purchase, title, username in purchases]}
        return json(purchases)

    @jwt_required
    @validate(json=PurchaseValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        """
        Implements POST method of REST API
        Requires JWT access token

        Changes the bill balance by the price of the product

        Args:
            request: {
                product_id: int
                user_id: int
                bill_id: int
                }
            *args:
            **kwargs:

        Returns: HTTP 201 Created and request body
        """
        session = request.ctx.session
        async with session.begin():
            bill = await session.execute(
                select(CustomerBillModel).where(CustomerBillModel.id == request.json.get('bill_id')))
            bill = bill.scalars().first()

            product = await session.execute(
                select(ProductModel).where(ProductModel.id == request.json.get('product_id')))
            product = product.scalars().first()

            if bill.balance < product.price:
                return json({'status': 400, 'msg': 'Not enough money to purchase'}, status=400)

            await session.execute(update(CustomerBillModel).values({'balance': bill.balance - product.price}).where(
                CustomerBillModel.id == request.json.get('bill_id')))
        return await super(PurchaseAPI, self).post(request, *args, **kwargs)


class PurchaseDetailAPI(BaseDetailAPI):
    """
    REST API for getting detailed information on a purchase and editing it
    """

    def __init__(self):
        super().__init__()
        self.model = PurchaseModel

    @jwt_required
    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Returns detailed information about the purchase, namely:
        - purchase id;
        - product_id;
        - title, which is taken from the associated Product table;
        - user_id;
        - username, which is taken from the associated User table;
        - bill_id.
        If the user is not the administrator and the record is not associated with the user, it returns an access error.
        If the record does not exist returns a missing data error.
        """
        session = request.ctx.session
        async with session.begin():
            if kwargs['token'].role == 'Admin':
                purchase = await session.execute(
                    select(PurchaseModel, ProductModel.title, User.username). \
                        join(ProductModel, ProductModel.id == PurchaseModel.product_id). \
                        join(User, User.id == PurchaseModel.user_id). \
                        where(PurchaseModel.id == pk))
            else:
                purchase = await session.execute(
                    select(PurchaseModel, ProductModel.title, User.username). \
                        join(ProductModel, ProductModel.id == PurchaseModel.product_id). \
                        join(User, User.id == PurchaseModel.user_id). \
                        where(PurchaseModel.id == pk, User.username == kwargs['token'].identity))
        if not purchase:
            return json({'status': 404, 'msg': 'Record does not exist'}, status=404)
        purchase, title, username = purchase.first()
        if (kwargs['token'].role == 'Admin') or (username == kwargs['token'].identity):
            purchase = {'id': purchase.id, 'user_id': purchase.user_id, "username": username,
                        'product_id': purchase.product_id, 'title': title, 'bill_id': purchase.bill_id}
            return json(purchase)
        else:
            return empty(status=403)

    @jwt_required(allow=['Admin'])
    @validate(json=PurchaseValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements PUT method of REST API
        Requires JWT access token and administrator rights
        Args:
            pk: int
            request: {
                product_id: int
                user_id: int
                bill_id: in
                }

        Returns: HTTP 200 OK | HTTP 201 Created
        """
        return await super(PurchaseDetailAPI, self).put(request, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements PATCH method of REST API
        Requires JWT access token and administrator rights
        Args:
            pk: int
            request: {
                product_id: Optional[int]
                user_id: Optional[int]
                bill_id: Optional[int]
                }

        Returns: HTTP 200 OK
        """
        return await super(PurchaseDetailAPI, self).patch(request, pk, *args, **kwargs)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements DELETE method of REST API
        Requires JWT access token and administrator rights
        """
        return await super(PurchaseDetailAPI, self).delete(request, pk, *args, **kwargs)
