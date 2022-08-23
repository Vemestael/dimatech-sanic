import sanic.response as response
from sanic import Blueprint

blueprint = Blueprint('dimatech_app')


@blueprint.route('/')
async def ping_me(request):
    return response.empty()
