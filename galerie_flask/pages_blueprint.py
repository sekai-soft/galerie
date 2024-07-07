import os
from functools import wraps
from sentry_sdk import capture_exception
from flask import Blueprint, redirect, render_template, g, request
from flask_babel import _
from galerie.feed_filter import FeedFilter
from galerie.image import extract_images, uid_to_item_id
from .helpers import requires_auth, compute_after_for_maybe_today, max_items, pocket_client, load_more_button_args, mark_as_read_button_args, images_args
from .get_aggregator import get_aggregator


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
            return render_template('error.html', error=str(e))
    return decorated_function


@pages_blueprint.route("/")
@catches_exceptions
@requires_auth
def index():
    if not g.aggregator.supports_get_unread_items_by_iid_descending():
        sort_by_desc = False
    else:
        sort_by_desc = request.args.get('sort', 'desc') == 'desc'
    today = request.args.get('today') == "1"
    group = request.args.get('group') if request.args.get('group') else None
    infinite_scroll = request.cookies.get('infinite_scroll', '0') == '1'

    selected_group = g.aggregator.get_group(group)
    groups = g.aggregator.get_groups()
    feed_filter = FeedFilter(compute_after_for_maybe_today(), group)
    if sort_by_desc:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(max_items, None, feed_filter)
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(max_items, None, feed_filter)
    images = extract_images(unread_items)
    last_iid_str = uid_to_item_id(images[-1].uid) if images else ''

    kwargs = {
        # today was used later soo...
        "all": not today,
        "selected_group": selected_group,
        "groups": groups,
        "supports_sort_desc": g.aggregator.supports_get_unread_items_by_iid_descending(),
        "sort_by_desc":sort_by_desc,
    }
    images_args(kwargs, images, pocket_client is not None)
    mark_as_read_button_args(kwargs, last_iid_str, today, group, sort_by_desc)
    load_more_button_args(kwargs, last_iid_str, today, group, sort_by_desc, infinite_scroll)

    return render_template('index.html', **kwargs)


@pages_blueprint.route("/login")
@catches_exceptions
def login():
    aggregator = get_aggregator()
    if aggregator:
        return redirect('/')
    return render_template(
        'login.html',
        fever_endpoint_help_url=_('https://github.com/sekai-soft/galerie?tab=readme-ov-file#example-fever-endpoints')
    )


@pages_blueprint.route("/settings")
@catches_exceptions
@requires_auth
def settings():
    infinite_scroll = request.cookies.get('infinite_scroll', '0') == '1'
    return render_template(
        'settings.html',
        connection_info=g.aggregator.connection_info(),
        infinite_scroll=infinite_scroll)
