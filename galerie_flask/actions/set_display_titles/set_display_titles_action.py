from flask import request, Blueprint, make_response
from galerie_flask.actions_blueprint import cookie_max_age


set_display_titles_bp = Blueprint('set_display_titles', __name__)


@set_display_titles_bp.route('/set_display_titles', methods=['POST'])
def set_display_titles():
    display_titles = request.form.get('display_titles', '1') == '1'

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    resp.set_cookie('display_titles', "1" if display_titles else "0", max_age=cookie_max_age)
    return resp
