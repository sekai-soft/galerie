import os
import json
import base64
from functools import wraps
from sentry_sdk import capture_exception
from flask import Blueprint, redirect, render_template, g, request, make_response
from flask_babel import _
from pocket import Pocket
from galerie.feed_filter import FeedFilter
from galerie.image import extract_images, uid_to_item_id
from galerie.inoreader_oauth import fetch_token
from .helpers import requires_auth, compute_after_for_maybe_today, max_items, get_pocket_client, load_more_button_args, mark_as_read_button_args, images_args, is_pocket_server_authenticated, add_image_ui_extras
from .get_aggregator import get_aggregator, check_inoreader_env, try_get_inoreader_aggregator


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
    for image in images:
        add_image_ui_extras(image)
    last_iid_str = uid_to_item_id(images[-1].uid) if images else ''

    kwargs = {
        "unread_count": g.aggregator.get_unread_items_count(feed_filter),
        # today was used later so has to use the key "all" instead of "today"
        "all": not today,
        "selected_group": selected_group,
        "groups": groups,
        "supports_sort_desc": g.aggregator.supports_get_unread_items_by_iid_descending(),
        "sort_by_desc":sort_by_desc,
    }
    images_args(kwargs, images, get_pocket_client() is not None)
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
    pocket_server_authenticated=is_pocket_server_authenticated()
    pocket_auth = json.loads(request.cookies.get('pocket_auth', '{}'))
    return render_template(
        'settings.html',
        connection_info=g.aggregator.connection_info(),
        pocket_server_authenticated=pocket_server_authenticated,
        pocket_auth=pocket_auth,
        infinite_scroll=infinite_scroll)


@pages_blueprint.route("/pocket_oauth")
@catches_exceptions
def pocket_oauth():
    consumer_key = os.environ['POCKET_CONSUMER_KEY']
    request_token = request.cookies.get('pocket_request_token')
    user_credentials = Pocket.get_credentials(consumer_key=consumer_key, code=request_token)

    resp = make_response(render_template(
        'pocket_oauth.html',
        username=user_credentials['username']))
    resp.delete_cookie('pocket_request_token')
    resp.set_cookie('pocket_auth', json.dumps(user_credentials))
    return resp


@pages_blueprint.route("/oauth/redirect")
@catches_exceptions
def oauth_redirect():
    if not check_inoreader_env():
        raise Exception('Inoreader environment variables not set')

    app_id = os.environ['INOREADER_APP_ID']
    inoreader_state = request.args.get('state')
    token = fetch_token(
        app_id,
        os.environ['INOREADER_APP_KEY'],
        os.environ['BASE_URL'],
        inoreader_state,
        request.url)
    
    inoreader_aggregator = try_get_inoreader_aggregator(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        expires_at=token['expires_at'])
    if not inoreader_aggregator:
        raise Exception('Failed to persist Inoreader configurations')

    persisted_auth = inoreader_aggregator.persisted_auth()
    auth_bytes = persisted_auth.encode("utf-8")
    b64_auth_bytes = base64.b64encode(auth_bytes)

    resp = make_response(redirect('/'))
    resp.set_cookie('auth', b64_auth_bytes.decode('utf-8'))
    return resp
