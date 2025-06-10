from flask import Blueprint, render_template, g, request
from galerie_flask.utils import DEFAULT_MAX_ITEMS, DEFAULT_MAX_RENDERED_ITEMS
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth


settings_bp = Blueprint('settings', __name__, template_folder='.')


@settings_bp.route("/settings")
@catches_exceptions
@requires_auth
def settings():
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    max_items = int(request.cookies.get('max_items', DEFAULT_MAX_ITEMS))
    max_rendered_items = int(request.cookies.get('max_rendered_items', DEFAULT_MAX_RENDERED_ITEMS))
    username = g.aggregator.get_username()
    connection_info = g.aggregator.connection_info()

    return render_template(
        'settings.html',
        infinite_scroll=infinite_scroll,
        max_items=max_items,
        max_rendered_items=max_rendered_items,
        username=username,
        connection_info=connection_info,
    )
