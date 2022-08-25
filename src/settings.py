from contextvars import ContextVar
from os import environ
from os.path import join, dirname

import dotenv
from sanic_jwt_extended.jwt_manager import JWT
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


class Settings(object):

    def __init__(self, app, filename='.env'):
        envpath = join(dirname(__file__), filename)
        dotenv.load_dotenv(envpath)

        self.SECRET_KEY = environ.get('SECRET_KEY')
        self.SIGNING_KEY = environ.get('SIGNING_KEY')
        self.DEBUG = environ.get('DEBUG')
        self.DB_NAME = environ.get('DB_NAME')
        self.DB_USER = environ.get('DB_USER')
        self.DB_PASSWORD = environ.get('DB_PASSWORD')
        self.DB_HOST = environ.get('DB_HOST')
        self.DB_PORT = environ.get('DB_PORT')
        self.DB_URL = f"postgresql+asyncpg://{self.DB_USER}:"f"{self.DB_HOST}@{self.DB_HOST}:{self.DB_PORT}" \
                      f"/{self.DB_NAME}"

        # call setup func
        self.setup_database(app)
        self.setup_jwt(app)

    def setup_database(self, app):
        bind = create_async_engine(self.DB_URL, echo=True)

        _base_model_session_ctx = ContextVar("session")

        @app.middleware("request")
        async def inject_session(request):
            request.ctx.session = sessionmaker(bind, AsyncSession, expire_on_commit=False)()
            request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)

        @app.middleware("response")
        async def close_session(request, response):
            if hasattr(request.ctx, "session_ctx_token"):
                _base_model_session_ctx.reset(request.ctx.session_ctx_token)
                await request.ctx.session.close()

    def setup_jwt(self, app):
        with JWT.initialize(app) as manager:
            manager.config.secret_key = self.SECRET_KEY
