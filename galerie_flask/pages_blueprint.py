from flask import Blueprint, redirect, render_template
from .helpers import get_aggregator, catches_exceptions


pages_blueprint = Blueprint('pages', __name__, static_folder='static', template_folder='templates')


@pages_blueprint.route("/login")
@catches_exceptions
def login():
    aggregator = get_aggregator()
    if aggregator:
        return redirect('/')
    return render_template('login.html')
