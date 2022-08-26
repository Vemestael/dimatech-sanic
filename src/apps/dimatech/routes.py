from sanic import Blueprint
import apps.dimatech.views as views

blueprint = Blueprint('dimatech_app', url_prefix='/api', version=1)

blueprint.add_route(views.ProductAPI.as_view(), '/products')
blueprint.add_route(views.ProductDetailAPI.as_view(), '/products/<pk:int>')

blueprint.add_route(views.CustomerBillAPI.as_view(), '/bills')
blueprint.add_route(views.CustomerBillDetailAPI.as_view(), '/bills/<pk:int>')

blueprint.add_route(views.TransactionAPI.as_view(), '/transactions')
blueprint.add_route(views.TransactionDetailAPI.as_view(), '/transactions/<pk:int>')

blueprint.add_route(views.PurchaseAPI.as_view(), '/purchases')
blueprint.add_route(views.PurchaseDetailAPI.as_view(), '/purchases/<pk:int>')
