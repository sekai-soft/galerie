from flask import Blueprint, render_template, g, request
from galerie_flask.utils import DEFAULT_MAX_ITEMS, DEFAULT_MAX_RENDERED_ITEMS, DEFAULT_INITIAL_PAGE_SIZE
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth


settings_bp = Blueprint('settings', __name__, template_folder='.')


@settings_bp.route("/settings")
@catches_exceptions
@requires_auth
def settings():
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    scroll_as_read = request.cookies.get('scroll_as_read', '0') == '1'
    display_titles = request.cookies.get('display_titles', '1') == '1'
    max_items = int(request.cookies.get('max_items', DEFAULT_MAX_ITEMS))
    initial_page_size = int(request.cookies.get('initial_page_size', DEFAULT_INITIAL_PAGE_SIZE))
    max_rendered_items = int(request.cookies.get('max_rendered_items', DEFAULT_MAX_RENDERED_ITEMS))
    username = g.aggregator.get_username()
    connection_info = g.aggregator.connection_info()

    return render_template(
        'settings.html',
        infinite_scroll=infinite_scroll,
        scroll_as_read=scroll_as_read,
        display_titles=display_titles,
        max_items=max_items,
        initial_page_size=initial_page_size,
        max_rendered_items=max_rendered_items,
        username=username,
        connection_info=connection_info,
    )
