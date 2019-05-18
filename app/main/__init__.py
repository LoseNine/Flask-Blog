from flask import Blueprint
from ..models import Permission

main=Blueprint('main',__name__)

from . import views,errors
#在本模板中全局可访问
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)