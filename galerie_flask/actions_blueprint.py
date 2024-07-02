import os
import json
import base64
from functools import wraps
from urllib.parse import unquote, unquote_plus, quote, quote_plus
from flask import request, g, Blueprint, make_response, render_template, Response
from flask_babel import _, lazy_gettext as _l
from sentry_sdk import capture_exception
from galerie.feed_filter import FeedFilter
from galerie.image import extract_images, uid_to_item_id
from galerie.rss_aggregator import AuthError
from .helpers import requires_auth, compute_after_for_maybe_today, get_aggregator, max_items, pocket_client

actions_blueprint = Blueprint('actions', __name__)


def make_toast_header(resp: Response, message: str):
    resp.headers['HX-Trigger'] = json.dumps({
        "toast": message
    })


def make_toast(status_code: int, message: str):
    resp = make_response()
    make_toast_header(resp, message)
    resp.status_code = status_code
    return resp


def catches_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            return make_toast(500, str(_l("Unknown server error: %(e)s", e=str(e))))
    return decorated_function


@actions_blueprint.route('/auth', methods=['POST'])
@catches_exceptions
def auth():
    endpoint = request.form.get('endpoint')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    try:
        persisted_auth = get_aggregator(
            logging_in_endpoint=endpoint,
            logging_in_username=username,
            logging_in_password=password).persisted_auth()
        auth_bytes = persisted_auth.encode("utf-8")
        b64_auth_bytes = base64.b64encode(auth_bytes)

        resp = make_response()
        resp.set_cookie('auth', b64_auth_bytes.decode('utf-8'))
        resp.headers['HX-Redirect'] = '/'
        return resp
    except AuthError:
        return make_toast(401, str(_("Failed to authenticate with Fever API")))


@actions_blueprint.route("/deauth", methods=['POST'])
@catches_exceptions
def deauth():
    resp = make_response()
    resp.delete_cookie('auth')
    resp.headers['HX-Redirect'] = '/login'
    return resp


@actions_blueprint.route('/load_more')
@catches_exceptions
@requires_auth
def load_more():
    if not g.aggregator.supports_get_unread_items_by_iid_descending():
        sort_by_desc = False
    else:
        sort_by_desc = request.args.get('sort', 'desc') == 'desc'

    group = request.args.get('group')
    from_iid = request.args.get('from_iid')
    feed_filter = FeedFilter(
        compute_after_for_maybe_today(),
        group
    )

    if sort_by_desc:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(
            max_items,
            from_iid,
            feed_filter)
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(
            max_items,
            from_iid,
            feed_filter)

    images = extract_images(unread_items)
    for image in images:
        image.ui_extra['quoted_url'] = quote(image.url)
        image.ui_extra['encoded_tags'] = ''.join(map(
            lambda g: f'&tag={quote_plus(g.title)}&tag={quote(f'group_id={g.gid}')}', image.groups)) if image.groups else ''

    last_iid_str = uid_to_item_id(images[-1].uid) if images else ''
    kwargs = {
        # args for image grid
        "images": images,
        "double_click_action": pocket_client is not None,
        # common args for both buttons
        'today_param': '&today=1' if request.args.get('today') == "1" else '',
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

    rendered_string = render_template('load_more.html', **kwargs)
    resp = make_response(rendered_string)
    if not images:
        make_toast_header(resp, str(_("All items were loaded")))
    return resp


@actions_blueprint.route('/mark_as_read', methods=['POST'])
@catches_exceptions
@requires_auth
def mark_as_read():
    if g.aggregator.supports_mark_items_as_read_by_iid_ascending_and_feed_filter():
        print(request.args.get('to_iid'))
        g.aggregator.mark_items_as_read_by_iid_ascending_and_feed_filter(
            request.args.get('to_iid'),
            FeedFilter(
                compute_after_for_maybe_today(),
                request.args.get('group')
            ))
    if g.aggregator.supports_mark_items_as_read_by_group_id():
        g.aggregator.mark_items_as_read_by_group_id(request.args.get('group'))

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/pocket', methods=['POST'])
@catches_exceptions
def pocket():
    if not pocket_client:
        return make_toast(500, str(_("Pocket was not configured")))
    encoded_url = request.args.get('url')
    url = unquote(encoded_url)
    encoded_tags = request.args.getlist('tag')
    tags = list(map(unquote_plus, encoded_tags))
    pocket_client.add(url, tags=','.join(tags))
    return make_toast(200, str(_l('Added %(url)s to Pocket', url=url)))
