from urllib.parse import urlparse
from flask import Blueprint, render_template, g, request
from flask_babel import _
from galerie.utils import get_base_url
from galerie_flask.utils import requires_auth
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth

bookmarklet = f"""javascript:(function() {{
  const url = `{get_base_url()}/add_feed?url=${{window.location.href}}&view_feed=1`;
  window.open(url, '_blank').focus();
}})();
"""


def is_valid_url(url: str) -> bool:
    try:
        urlparse(url)
        return True
    except ValueError:
        return False


add_feed_bp = Blueprint('add_feed', __name__, template_folder='.')


@add_feed_bp.route("/add_feed")
@catches_exceptions
@requires_auth
def add_feed_page():   
    args = request.args
    url = None
    if 'url' in args and is_valid_url(args['url']):
        url = args['url']
    elif 'text' in args and is_valid_url(args['text']):
        url = args['text']
    elif 'title' in args and is_valid_url(args['title']):
        url = args['title']

    add_feed_behavior = ''
    if args.get('view_feed', '0')== '1':
        add_feed_behavior += '?view_feed=1'
    if args.get('go_home', '0') == '1':
        add_feed_behavior += '?go_home=1'
    if args.get('show_toast', '0') == '1':
        add_feed_behavior += '?show_toast=1'

    default_group = args.get('group')

    return render_template(
        'add_feed.html',
        url=url,
        bookmarklet=bookmarklet,
        groups=g.aggregator.get_groups(),
        add_feed_behavior=add_feed_behavior,
        default_group=default_group
    )
