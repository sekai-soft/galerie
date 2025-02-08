import os
import json
import base64
import qrcode
from functools import wraps
from urllib.parse import unquote, unquote_plus
from io import BytesIO
from flask import request, g, Blueprint, make_response, render_template, Response, send_file
from flask_babel import _, lazy_gettext as _l
from sentry_sdk import capture_exception
from pocket import Pocket
from galerie.feed_filter import FeedFilter
from galerie.image import extract_images, uid_to_item_id
from galerie.rss_aggregator import AuthError
from .utils import requires_auth, compute_after_for_maybe_today, max_items, get_pocket_client, load_more_button_args, mark_as_read_button_args, images_args, add_image_ui_extras, encode_setup_from_cookies, decode_setup_to_cookies
from .get_aggregator import get_aggregator

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
    if 'setup-code' in request.form and request.form['setup-code']:
        resp = make_response()
        setup_code = request.form['setup-code']
        setup_code = base64.b64decode(setup_code)
        setup_code = setup_code.decode("utf-8")
        decode_setup_to_cookies(setup_code, resp)
        resp.headers['HX-Redirect'] = '/'
        return resp

    endpoint = request.form.get('endpoint')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    aggregator_type = request.form.get('type', 'miniflux')
    try:
        aggregator = get_aggregator(
            logging_in_endpoint=endpoint,
            logging_in_username=username,
            logging_in_password=password,
            aggregator_type=aggregator_type)
        if not aggregator:
            raise AuthError()
        persisted_auth = aggregator.persisted_auth()

        resp = make_response()
        resp.set_cookie('auth', persisted_auth)
        resp.headers['HX-Redirect'] = '/'
        return resp
    except AuthError:
        return make_toast(401, str(_("Failed to authenticate")))


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
    sort_by_desc = request.args.get('sort', 'desc') == 'desc'
    today = request.args.get('today') == "1"
    group = request.args.get('group') if request.args.get('group') else None
    from_iid = request.args.get('from_iid')
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
   
    feed_filter = FeedFilter(compute_after_for_maybe_today(), group)
    if sort_by_desc:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(max_items, from_iid, feed_filter)
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(max_items, from_iid, feed_filter)
    images = extract_images(unread_items)
    for image in images:
        add_image_ui_extras(image)
    last_iid_str = uid_to_item_id(images[-1].uid) if images else ''

    args = {}
    images_args(args, images, get_pocket_client() is not None)
    mark_as_read_button_args(args, last_iid_str, today, group, sort_by_desc)
    load_more_button_args(args, last_iid_str, today, group, sort_by_desc, infinite_scroll)

    rendered_string = render_template('load_more.html', **args)
    resp = make_response(rendered_string)
    if not images:
        make_toast_header(resp, str(_("All items were loaded")))
    return resp


@actions_blueprint.route('/mark_as_read', methods=['POST'])
@catches_exceptions
@requires_auth
def mark_as_read():
    group = request.args.get('group') if request.args.get('group') else None
    g.aggregator.mark_items_as_read_by_group_id(group)

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/pocket', methods=['POST'])
@catches_exceptions
def pocket():
    pocket_client = get_pocket_client()
    if not pocket_client:
        return make_toast(400, str(_("Pocket was not configured")))
    encoded_url = request.args.get('url')
    url = unquote(encoded_url)
    encoded_tags = request.args.getlist('tag')
    tags = list(map(unquote_plus, encoded_tags))
    pocket_client.add(url, tags=','.join(tags))
    return make_toast(200, str(_l('Added %(url)s to Pocket', url=url)))


@actions_blueprint.route('/set_infinite_scroll', methods=['POST'])
@catches_exceptions
def set_infinite_scroll():
    infinite_scroll = request.form.get('infinite_scroll', '0')
    resp = make_response()
    resp.set_cookie('infinite_scroll', infinite_scroll)
    make_toast_header(resp, _("Setting updated"))
    return resp


@actions_blueprint.route('/connect_to_pocket', methods=['POST'])
@catches_exceptions
def connect_to_pocket():
    if 'POCKET_CONSUMER_KEY' not in os.environ:
        return make_toast(500, str(_("Pocket consumer key was not configured")))
    consumer_key = os.environ['POCKET_CONSUMER_KEY']

    if 'BASE_URL' not in os.environ:
        return make_toast(500, str(_("Base URL was not configured")))
    redirect_uri = os.environ['BASE_URL'] + '/pocket_oauth'

    request_token = Pocket.get_request_token(
        consumer_key=consumer_key,
        redirect_uri=redirect_uri)
    auth_url = Pocket.get_auth_url(
        code=request_token,
        redirect_uri=redirect_uri)

    resp = make_response()
    resp.set_cookie('pocket_request_token', request_token)
    resp.headers['HX-Redirect'] = auth_url
    return resp


@actions_blueprint.route('/disconnect_from_pocket', methods=['POST'])
@catches_exceptions
def disconnect_from_pocket():
    resp = make_response()
    resp.delete_cookie('pocket_request_token')
    resp.delete_cookie('pocket_auth')
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/qrcode.jpg', methods=['GET'])
@catches_exceptions
def _qrcode():
    if 'auth' not in request.cookies:
        return make_toast(401, str(_("Not authenticated")))

    img = qrcode.make(encode_setup_from_cookies())

    img_io = BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg')


@actions_blueprint.route('/convert_to_image_feed', methods=['POST'])
@catches_exceptions
def convert_to_image_feed():
    feed = request.args.get('feed') if request.args.get('feed') else None
    if not feed:
        return make_toast(400, "Feed was not provided")
    aggregator = get_aggregator()
    if not aggregator:
        return make_toast(400, "Aggregator was not configured")
    aggregator.convert_to_image_feed(feed)
    return make_toast(200, "Feed was converted to image feed")


@actions_blueprint.route('/unconvert_from_image_feed', methods=['POST'])
@catches_exceptions
def unconvert_from_image_feed():
    feed = request.args.get('feed') if request.args.get('feed') else None
    if not feed:
        return make_toast(400, "Feed was not provided")
    aggregator = get_aggregator()
    if not aggregator:
        return make_toast(400, "Aggregator was not configured")
    aggregator.unconvert_from_image_feed(feed)
    return make_toast(200, "Feed was unconverted from image feed")
