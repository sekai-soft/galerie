from flask import request, Blueprint, make_response
from flask_babel import _
from galerie_flask.actions_blueprint import cookie_max_age


set_no_text_mode_bp = Blueprint('set_no_text_mode', __name__)

@set_no_text_mode_bp.route('/set_no_text_mode', methods=['POST'])
def set_no_text_mode():
    no_text_mode = request.form.get('no_text_mode', '0') == '1'

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    resp.set_cookie('no_text_mode', "1" if no_text_mode else "0", max_age=cookie_max_age)
    return resp
