from flask import request, Blueprint
from flask_babel import _
from galerie_flask.utils import DEFAULT_MAX_ITEMS
from galerie_flask.actions_blueprint import make_toast, cookie_max_age


set_max_items_bp = Blueprint('set_max_items', __name__)


@set_max_items_bp.route('/set_max_items', methods=['POST'])
def set_max_items():
    max_items = request.form.get('max_items', DEFAULT_MAX_ITEMS)

    resp = make_toast(200, _("Setting updated"))
    resp.set_cookie('max_items', max_items, max_age=cookie_max_age)
    return resp
