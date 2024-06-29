import os
from functools import wraps
from sentry_sdk import capture_exception
from flask import Blueprint, redirect, render_template, make_response, g, request
from flask_babel import _, lazy_gettext as _l
from galerie.feed_filter import FeedFilter
from galerie.image import extract_images, uid_to_item_id
from .helpers import get_aggregator, requires_auth, compute_after_for_maybe_today, max_items, pocket_client


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
    group = request.args.get('group')

    feed_filter = FeedFilter(
        compute_after_for_maybe_today(),
        group)
    if sort_by_desc:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(
            max_items,
            None,
            feed_filter)
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(
            max_items,
            None,
            feed_filter)

    images = extract_images(unread_items)
    groups = g.aggregator.get_groups()
    selected_group = g.aggregator.get_group(group)
    supports_sort_desc = g.aggregator.supports_get_unread_items_by_iid_descending()

    last_iid_str = uid_to_item_id(images[-1].uid) if images else ''
    kwargs = {
        # args for header
        "today": today,
        "selected_group": selected_group,
        "groups": groups,
        "supports_sort_desc": supports_sort_desc,
        "sort_by_desc": sort_by_desc,
        # args for image grid
        "images": images,
        "double_click_action": pocket_client is not None,
        # common args for both buttons
        'today_param': '&today=1' if today else '',
        'gid_param': group if group else '',
        'sort_param': '&sort=desc' if sort_by_desc else '&sort=asc',
        # args for mark as read button
        'to_iid': last_iid_str,
        # args for load more button
        'from_iid': last_iid_str,
    }
    if g.aggregator.supports_mark_items_as_read_by_iid_ascending_and_feed_filter():
        kwargs['mark_as_read_confirm'] = _('Are you sure you want to mark above as read?')
    else:
        kwargs['mark_as_read_confirm'] = _('Are you sure you want to mark current group as read? It will mark still undisplayed entries as read as well.')

    return render_template('index.html', **kwargs)


@pages_blueprint.route("/login")
@catches_exceptions
def login():
    aggregator = get_aggregator()
    if aggregator:
        return redirect('/')
    return render_template('login.html')
