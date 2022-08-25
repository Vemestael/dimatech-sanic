from sanic import Blueprint
import apps.auth.views as views

blueprint = Blueprint('auth_app', url_prefix='/auth', version=1)

blueprint.add_route(views.UserAPI.as_view(), '/user')
blueprint.add_route(views.UserDetailAPI.as_view(), '/user/<pk:int>')
blueprint.add_route(views.activate_account, '/activate/<token:str>')
blueprint.add_route(views.login, '/login/', methods=['POST'])
blueprint.add_route(views.get_refresh_token, '/refresh/', methods=['POST'])
