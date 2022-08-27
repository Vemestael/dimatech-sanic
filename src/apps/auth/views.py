from hashlib import pbkdf2_hmac
from os import urandom

import jwt
from sanic import Sanic, Request, response
from sanic.response import json, empty
from sanic.views import HTTPMethodView
from sanic_ext import validate
from sanic_jwt_extended import JWT
from sanic_jwt_extended.decorators import refresh_jwt_required, jwt_required
from sanic_jwt_extended.tokens import Token
from sqlalchemy import select, update, delete

from apps.auth.models import User, UserValidator, UserDetailValidator


async def get_password_hash(password: str) -> tuple:
    salt = urandom(32)

    password_hash = pbkdf2_hmac(hash_name='sha256', password=password.encode('utf-8'), salt=salt, iterations=100000)
    return salt, password_hash


async def check_password(salt, current_password_hash, new_password: str) -> bool:
    password_hash = pbkdf2_hmac(hash_name='sha256', password=new_password.encode('utf-8'), salt=salt, iterations=100000)
    return current_password_hash == password_hash


class UserAPI(HTTPMethodView):
    @jwt_required(allow=['Admin'])
    async def get(self, request: Request, *args, **kwargs) -> response:
        """
        Args:
            request: None
            *args: None
            **kwargs: token

        Returns: List of users
        """
        session = request.ctx.session
        async with session.begin():
            users = await session.execute(select(User).order_by(User.id))
        users = users.scalars().all()
        users = {'users': [{'username': user.username, 'is_active': user.is_active} for user in users]}
        return json(users)

    @validate(json=UserValidator)
    async def post(self, request: Request, *args, **kwargs) -> response:
        """
        Creates a new user in the inactive state and generates an activation link
        Args:
            request: {
                username: str = Field(max_length=150)
                password: str = Field(min_length=8)
                email: Optional[EmailStr]
                is_active: Optional[bool]
                is_admin: Optional[bool]
                }
            *args:
            **kwargs:

        Returns: activation_url
        """
        host = request.headers.get('host')

        session = request.ctx.session
        async with session.begin():
            _salt, _password = await get_password_hash(request.json.get('password'))
            user = User(username=request.json.get('username').lower(), password_hash=_password, salt=_salt,
                        email=request.json.get('email', ''))
            session.add(user)

        activation_url = f'http://{host}/v1/auth/activate/' \
                         f'{jwt.encode({"user_id": user.id}, Sanic.get_app().config.SECRET_KEY).decode("utf-8")}/'
        return json(activation_url, status=201)


class UserDetailAPI(HTTPMethodView):
    """
    The class provides basic endpoints for getting detailed information about the User and editing it
    """
    @jwt_required(allow=['User', 'Admin'])
    async def get(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements the GET method for the REST API
        """
        session = request.ctx.session
        async with session.begin():
            user = await session.execute(select(User).where(User.id == pk))
        user = user.scalars().first()
        user = {'username': user.username, 'email': user.email, 'is_active': user.is_active, 'is_admin': user.is_admin}
        return json(user)

    @jwt_required(allow=['Admin'])
    @validate(json=UserValidator)
    async def put(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements the PUT method for the REST API
        """
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

    @jwt_required(allow=['Admin'])
    @validate(json=UserDetailValidator)
    async def patch(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements the PATCH method for the REST API
        """
        session = request.ctx.session
        user_data = request.json.copy()

        async with session.begin():
            if user_data.get('password'):
                salt, password_hash = await get_password_hash(user_data.pop('password'))
                user_data.update({'salt': salt, 'password_hash': password_hash})

            await session.execute(update(User).values(**user_data).where(User.id == pk))
        return json(request.json, status=200)

    @jwt_required(allow=['Admin'])
    async def delete(self, request: Request, pk: int, *args, **kwargs) -> response:
        """
        Implements the DELETE method for the REST API
        """
        session = request.ctx.session
        async with session.begin():
            await session.execute(delete(User).where(User.id == pk))
        return empty(status=200)


async def activate_account(request: Request, token: str, *args, **kwargs) -> response:
    """
    Activates the account by the ID obtained from the decrypted token
    Args:
        request: None
        token: derived from the url
        *args: None
        **kwargs: None

    Returns: HTTP 204 No Content
    """
    pk = jwt.decode(token, Sanic.get_app().config.SECRET_KEY)['user_id']
    # here you can make a lot of protections, such as adding token lifetime
    # or putting tokens in a separate table, and after activation delete them
    session = request.ctx.session
    async with session.begin():
        await session.execute(update(User).values({'is_active': True}).where(User.id == pk))
    return empty()


@validate(json=UserValidator)
async def login(request: Request, *args, **kwargs) -> response:
    """
    Authorizes the user in the system via JWT
    Args:
        request: {
            username: str = Field(max_length=150)
            password: str = Field(min_length=8)
            }
        *args:
        **kwargs:

    Returns: Error or JWT access and refresh tokens
    """
    username = request.json.get('username')
    password = request.json.get('password')

    session = request.ctx.session

    async with session.begin():
        user = await session.execute(select(User).where(User.username == username))
    user = user.scalars().first()

    if not user.is_active:
        return json({'status': 400, 'message': 'User disabled'}, status=400)

    if await check_password(user.salt, user.password_hash, password):
        if user.is_admin:
            role = 'Admin'
        else:
            role = 'User'

        access_token = JWT.create_access_token(identity=username, role=role)
        refresh_token = JWT.create_refresh_token(identity=username, role=role)
        return json({'access_token': access_token, 'refresh_token': refresh_token}, status=201)
    else:
        return json({'status': 400, 'message': 'Wrong user data'}, status=400)


@refresh_jwt_required
async def get_refresh_token(request: Request, token: Token) -> response:
    """
    Generates a new JWT access token
    Args:
        request: None
        token: Taken from the "X-Refresh-Token" header to look for the refresh JWT

    Returns: access_token
    """
    return json({"access_token": JWT.create_access_token(identity=token.identity)})


@jwt_required
async def revoke_token(request, *args, **kwargs):
    """
    Revoke specific token
    Args:
        request: {
            token: str
            }
        *args:
        **kwargs:

    Returns: HTTP 204 No Content
    """
    await Token(request.json.get('token')).revoke()
    return empty()
