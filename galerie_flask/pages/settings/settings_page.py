from flask import Blueprint, render_template, g, request
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth


settings_bp = Blueprint('settings', __name__, template_folder='.')


@settings_bp.route("/settings")
@catches_exceptions
@requires_auth
def settings():
    connection_info = g.aggregator.connection_info()
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    username = g.aggregator.get_username()
    
    return render_template(
        'settings.html',
        connection_info=connection_info,
        infinite_scroll=infinite_scroll,
        username=username,
    )
