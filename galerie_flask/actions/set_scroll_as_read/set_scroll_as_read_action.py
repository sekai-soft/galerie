from flask import request, Blueprint, make_response
from galerie_flask.actions_blueprint import cookie_max_age


set_scroll_as_read_bp = Blueprint('set_scroll_as_read', __name__)

@set_scroll_as_read_bp.route('/set_scroll_as_read', methods=['POST'])
def set_scroll_as_read():
    scroll_as_read = request.form.get('scroll_as_read', '0') == '1'

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    resp.set_cookie('scroll_as_read', "1" if scroll_as_read else "0", max_age=cookie_max_age)
    return resp
