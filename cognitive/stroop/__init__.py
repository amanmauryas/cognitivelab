from flask import Blueprint

stroop_bp = Blueprint(
    'stroop',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/stroop/static'
)

from . import routes
