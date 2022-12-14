import argparse

from sanic import Sanic

from apps.auth import blueprint as auth_app
from apps.dimatech import blueprint as dimatech_app
from apps.payment import blueprint as payment_app
from core.extentions.exceptions import blueprint as ext_exceptions
from core.extentions.middlewares import blueprint as ext_middlewares
from settings import Settings


# Configure Sanic apps
app = Sanic(__name__)

settings = Settings(app)
app.update_config(settings)

# Install extentions
app.blueprint(ext_exceptions)
app.blueprint(ext_middlewares)

# Install apps
app.blueprint(auth_app)
app.blueprint(dimatech_app)
app.blueprint(payment_app)

# Command line parser options & setup default values
parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Setup host ip to listen up, default to 0.0.0.0', default='0.0.0.0')
parser.add_argument('--port', help='Setup port to attach, default to 8080', type=int, default=8000)
parser.add_argument('--workers', help='Setup workers to run, default to 1', type=int, default=1)
parser.add_argument('--debug', help='Enable or disable debugging', default=app.config.DEBUG)
parser.add_argument('--accesslog', help='Enable or disable access log', default=app.config.DEBUG)
args = parser.parse_args()

# Running sanic, we need to make sure directly run by interpreter
# ref: http://sanic.readthedocs.io/en/latest/sanic/deploying.html#running-via-command
if __name__ == '__main__':
    app.run(
        host=args.host,
        port=args.port,
        workers=args.workers,
        debug=args.debug,
        auto_reload=args.debug,
        access_log=args.accesslog
    )
