from hashlib import pbkdf2_hmac
from os import urandom

import jwt
from sanic import Sanic, Request, response
from sanic.response import json, empty
from sanic.views import HTTPMethodView
from sanic_ext import validate
from sanic_jwt_extended import JWT
from sanic_jwt_extended.decorators import refresh_jwt_required
from sanic_jwt_extended.tokens import Token
from sqlalchemy import select, update, delete

from apps.auth.models import User, UserValidator, UserDetailValidator, AuthorizationValidator


async def get_password_hash(password: str) -> tuple:
    salt = urandom(32)

    password_hash = pbkdf2_hmac(
        hash_name='sha256',
        password=password.encode('utf-8'),
        salt=salt,
        iterations=100000  # It is recommended to use at least 100,000 iterations of SHA-256
    )
    return salt, password_hash


async def check_password(salt, current_password_hash, new_password: str) -> bool:
    password_hash = pbkdf2_hmac(
        'sha256',
        new_password.encode('utf-8'),
        salt,
        100000  # It is recommended to use at least 100,000 iterations of SHA-256
    )
    return current_password_hash == password_hash


class UserAPI(HTTPMethodView):
    async def get(self, request: Request, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            users = await session.execute(select(User).order_by(User.id))
        users = users.scalars().all()
        users = {'users': [{'username': user.username, 'is_active': user.is_active} for user in users]}
        return json(users)

    @validate(json=UserValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        host = request.headers.get('host')

        session = request.ctx.session
        async with session.begin():
            _salt, _password = await get_password_hash(request.json.get('password'))
            user = User(username=request.json.get('username'), password_hash=_password, salt=_salt,
                        email=request.json.get('email', ''))
            session.add(user)

        activation_url = f'http://{host}/v1/auth/activate/' \
                         f'{jwt.encode({"user_id": user.id}, Sanic.get_app().config.SECRET_KEY).decode("utf-8")}/'
        return json(activation_url, status=201)


class UserDetailAPI(HTTPMethodView):

    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            user = await session.execute(select(User).where(User.id == pk))
        user = user.scalars().first()
        user = {'username': user.username, 'email': user.email, 'is_active': user.is_active, 'is_admin': user.is_admin}
        return json(user)

    @validate(json=UserValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        user_data = request.json.copy()

        salt, password_hash = await get_password_hash(user_data.pop('password'))
        user_data.update({'salt': salt, 'password_hash': password_hash})

        async with session.begin():
            user = await session.execute(select(User).where(User.id == pk))
            if user.scalar_one_or_none():
                await session.execute(update(User).values(**user_data).where(User.id == pk))
                return json(request.json, status=200)
            else:
                user = User(**user_data)
                session.add(user)
                return json(request.json, status=201)

    @validate(json=UserDetailValidator)
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        user_data = request.json.copy()

        async with session.begin():
            if user_data.get('password'):
                salt, password_hash = await get_password_hash(user_data.pop('password'))
                user_data.update({'salt': salt, 'password_hash': password_hash})

            await session.execute(update(User).values(**user_data).where(User.id == pk))
        return json(request.json, status=200)

    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        session = request.ctx.session
        async with session.begin():
            await session.execute(delete(User).where(User.id == pk))
        return empty(status=200)


async def activate_account(request: Request, token: str, *args, **kwargs) -> response:
    pk = jwt.decode(token, Sanic.get_app().config.SECRET_KEY)['user_id']
    # here you can make a lot of protections, such as adding token lifetime
    # or putting tokens in a separate table, and after activation delete them
    session = request.ctx.session
    async with session.begin():
        await session.execute(update(User).values({'is_active': True}).where(User.id == pk))
    return empty()


@validate(json=UserValidator)
async def login(request: Request, *args, **kwargs) -> response:
    username = request.json.get('username')
    password = request.json.get('password')

    session = request.ctx.session

    async with session.begin():
        user = await session.execute(select(User).where(User.username == username))
    user = user.scalars().first()
    if await check_password(user.salt, user.password_hash, password):
        access_token = JWT.create_access_token(identity=username)
        refresh_token = JWT.create_refresh_token(identity=username)
        return json({'access_token': access_token, 'refresh_token': refresh_token}, status=201)
    else:
        return json({'status': 400, 'message': 'Wrong user data'}, status=400)


@refresh_jwt_required
async def get_refresh_token(request: Request, token: Token) -> response:
    return json({"refresh_token": JWT.create_access_token(identity=token.identity)})
