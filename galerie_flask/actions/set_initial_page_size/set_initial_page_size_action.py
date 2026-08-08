from flask import request, Blueprint
from flask_babel import _
from galerie_flask.utils import DEFAULT_INITIAL_PAGE_SIZE
from galerie_flask.actions_blueprint import make_toast, cookie_max_age


set_initial_page_size_bp = Blueprint('set_initial_page_size', __name__)


@set_initial_page_size_bp.route('/set_initial_page_size', methods=['POST'])
def set_initial_page_size():
    initial_page_size = request.form.get('initial_page_size', DEFAULT_INITIAL_PAGE_SIZE)

    resp = make_toast(200, _("Setting updated"))
    resp.set_cookie('initial_page_size', initial_page_size, max_age=cookie_max_age)
    return resp
