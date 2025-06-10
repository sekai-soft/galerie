from flask import Blueprint, render_template, g, request
from flask_babel import _
from galerie.rendered_item import convert_rendered_items
from galerie_flask.utils import requires_auth, items_args, DEFAULT_MAX_RENDERED_ITEMS
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth


feed_bp = Blueprint('feed', __name__, template_folder='.')


@feed_bp.route("/feed")
@catches_exceptions
@requires_auth
def feed_page():
    fid = request.args.get('fid')
    feed = g.aggregator.get_feed(fid)
    feed_icon = None
    if feed:
        feed_icon = g.aggregator.get_feed_icon(fid)

    max_rendered_items = int(request.cookies.get('max_rendered_items', DEFAULT_MAX_RENDERED_ITEMS))

    items = g.aggregator.get_feed_items_by_iid_descending(fid)
    rendered_items = convert_rendered_items(items, max_rendered_items)

    args = {
        "feed": feed,
        "feed_icon": feed_icon,
        "context_feed_page": True,
    }
    items_args(args, rendered_items, False, False)
    return render_template('feed.html', **args)
