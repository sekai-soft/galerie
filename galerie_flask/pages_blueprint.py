from flask import Blueprint, redirect, render_template
from .helpers import get_aggregator, catches_exceptions


login_blueprint = Blueprint('login', __name__, static_folder='static', template_folder='templates')


@login_blueprint.route("/login")
@catches_exceptions
def login():
    aggregator = get_aggregator()
    if aggregator:
        return redirect('/')
    return render_template('login.html')
