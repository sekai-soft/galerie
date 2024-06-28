import os
from functools import wraps
from sentry_sdk import capture_exception
from flask import Blueprint, redirect, render_template, make_response
from flask_babel import lazy_gettext as _l
from .helpers import get_aggregator


pages_blueprint = Blueprint('pages', __name__, static_folder='static', template_folder='templates')


def catches_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            resp = make_response(_l("Unknown server error: %(e)s", e=str(e)))
            resp.status_code = 500
            return resp
    return decorated_function


@pages_blueprint.route("/login")
@catches_exceptions
def login():
    aggregator = get_aggregator()
    if aggregator:
        return redirect('/')
    return render_template('login.html')
