import os
import json
import base64
import requests
from functools import wraps
from urllib.parse import unquote, unquote_plus
from flask import request, g, Blueprint, make_response, render_template, Response
from flask_babel import _, lazy_gettext as _l
from sentry_sdk import capture_exception
from pocket import Pocket
from requests.auth import HTTPBasicAuth
from galerie.feed_filter import FeedFilter
from galerie.rendered_item import convert_rendered_items
from galerie.rss_aggregator import AuthError
from galerie.parse_feed_features import is_nitter_on_fly, extract_nitter_on_fly
from .utils import requires_auth, max_items, get_pocket_client,\
    load_more_button_args, mark_as_read_button_args, items_args, add_image_ui_extras,\
    decode_setup_to_cookies, is_instapaper_available, get_instapaper_auth, cookie_max_age
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
    next_url = request.args.get('next', '/')

    if 'setup-code' in request.form and request.form['setup-code']:
        resp = make_response()
        setup_code = request.form['setup-code']
        setup_code = base64.b64decode(setup_code)
        setup_code = setup_code.decode("utf-8")
        decode_setup_to_cookies(setup_code, resp)
        resp.headers['HX-Redirect'] = next_url
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
        resp.set_cookie('auth', persisted_auth, max_age=cookie_max_age)
        resp.headers['HX-Redirect'] = next_url
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
    from_iid = request.args.get('from_iid')
    gid = request.args.get('group') if request.args.get('group') else None
    sort_by = request.args.get('sort', 'desc') == 'desc'
    remaining_count = int(request.args.get('remaining_count'))
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
   
    feed_filter = FeedFilter(gid)
    if sort_by:
        unread_items = g.aggregator.get_unread_items_by_iid_descending(max_items, from_iid, feed_filter)
    else:
        unread_items = g.aggregator.get_unread_items_by_iid_ascending(max_items, from_iid, feed_filter)
    
    rendered_items = convert_rendered_items(unread_items)
    for rendered_item in rendered_items:
        add_image_ui_extras(rendered_item)
    last_iid = unread_items[-1].iid if unread_items else ''    

    if last_iid:
        args = {}
        items_args(args, rendered_items, gid is None)
        load_more_button_args(args, last_iid, gid, sort_by, infinite_scroll, remaining_count - max_items)
        rendered_string = \
            render_template('items_stream.html', **args) + "\n" + \
            render_template('load_more_button.html', **args)
    else:
        args = {}
        mark_as_read_button_args(args, gid, sort_by)
        rendered_string = render_template('all_loaded_marker.html', **args)

    resp = make_response(rendered_string)
    resp.headers['HX-Trigger-After-Settle'] = json.dumps({
        "append": list(map(lambda i: i.uid, rendered_items))
    })
    return resp


@actions_blueprint.route('/mark_as_read', methods=['POST'])
@catches_exceptions
@requires_auth
def mark_as_read():
    group = request.args.get('group') if request.args.get('group') else None
    if group:
        g.aggregator.mark_all_group_items_as_read(group)
    else:
        g.aggregator.mark_all_items_as_read()

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/pocket', methods=['POST'])
@catches_exceptions
def pocket():
    pocket_client = get_pocket_client()
    if not pocket_client:
        return make_toast(400, "Pocket was not configured")

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
    resp.set_cookie('infinite_scroll', infinite_scroll, max_age=cookie_max_age)
    make_toast_header(resp, _("Setting updated"))
    return resp


@actions_blueprint.route('/connect_to_pocket', methods=['POST'])
@catches_exceptions
def connect_to_pocket():
    if 'POCKET_CONSUMER_KEY' not in os.environ:
        return make_toast(500, "Pocket consumer key was not configured")
    consumer_key = os.environ['POCKET_CONSUMER_KEY']

    if 'BASE_URL' not in os.environ:
        return make_toast(500, "Base URL was not configured")
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


@actions_blueprint.route('/update_feed_group', methods=['POST'])
@requires_auth
@catches_exceptions
def update_feed_group():
    fid = request.args.get('fid')
    if fid is None:
        return make_toast(400, "fid is required")

    group = request.form.get('update_feed_group')
    if group is None:
        return make_toast(400, "Group id is required")
    
    g.aggregator.update_feed_group(fid, group)
    return make_toast(200, str(_("Group updated")))


@actions_blueprint.route('/add_feed', methods=['POST'])
@requires_auth
@catches_exceptions
def add_feed():
    if 'group' not in request.form:
        return make_toast(400, "Group is required")
    gid = request.form.get('group')
    
    feed_url = None
    if 'twitter_handle' in request.form:
        twitter_handle = request.form["twitter_handle"]
        twitter_handle = twitter_handle[1:] if twitter_handle[0] == '@' else twitter_handle

        # find a nitter-on-fly feed
        for feed in g.aggregator.get_feeds():
            f_url = feed.features['feed_url']
            if is_nitter_on_fly(f_url):
                domain, password = extract_nitter_on_fly(f_url)
                break
               
        if domain and password:
            feed_url = f'https://{domain}/{twitter_handle}/rss?key={password}'
        else:
            return make_toast(400, "Cannot find an existing nitter-on-fly feed")
    elif 'url' in request.form:
        feed_url = request.form['url']

    if not feed_url:
        return make_toast(400, "URL is required")
    try:
        fid = g.aggregator.add_feed(feed_url, gid)
        g.aggregator.mark_all_feed_items_as_read(fid)
    except Exception as e:
        # TODO: this is miniflux specific
        return make_toast(400, e.get_error_reason())

    if fid:
        resp = make_response()
        resp.headers['HX-Redirect'] = f'/feed?fid={fid}'
        return resp
    return make_toast(400, "Failed to add feed")


@actions_blueprint.route('/delete_feed', methods=['POST'])
@requires_auth
@catches_exceptions
def delete_feed():
    if 'fid' not in request.args:
        return make_toast(400, "Feed is required")

    fid = request.args.get('fid')
    g.aggregator.delete_feed(fid)

    resp = make_response()
    resp.headers['HX-Redirect'] = '/feeds'
    return resp


@actions_blueprint.route('/log_into_instapaper', methods=['POST'])
@catches_exceptions
def log_into_instapaper():
    username_or_email = request.form.get('username_or_email')
    if not username_or_email:
        return make_toast(400, _("Instapaper username or email is required"))

    password = request.form.get('password', '')

    auth_res = requests.post("https://www.instapaper.com/api/authenticate", data={
        "username": username_or_email,
        "password": password
    })
    if auth_res.status_code != 200:
        return make_toast(400, _("Failed to log into Instapaper"))

    resp = make_response()
    resp.set_cookie('instapaper_auth', json.dumps({
        'username_or_email': username_or_email,
        'password': password
    }), max_age=cookie_max_age)
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/log_out_of_instapaper', methods=['POST'])
@catches_exceptions
def log_out_of_instapaper():
    resp = make_response()
    resp.delete_cookie('instapaper_auth')
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/instapaper', methods=['POST'])
@catches_exceptions
def instapaper():
    if not is_instapaper_available():
        return make_toast(400, "Instapaper was not configured")
    username_or_email, password = get_instapaper_auth()

    encoded_url = request.args.get('url')
    url = unquote(encoded_url)

    add_res = requests.post(
        "https://www.instapaper.com/api/add",
        auth=HTTPBasicAuth(username_or_email, password),
        data={"url": url}
    )
    if add_res.status_code != 201:
        return make_toast(400, _('Failed to add to Instapaper',))
    return make_toast(200, str(_l('Added %(url)s to Instapaper', url=url)))


@actions_blueprint.route('/mark_last_unread', methods=['POST'])
@requires_auth
@catches_exceptions
def mark_last_unread():
    if os.getenv('DEBUG', '0') != '1':
        return make_toast(400, "This endpoint is only available in debug mode")
    if 'count' not in request.args:
        return make_toast(400, "Count is required")

    count = int(request.args.get('count'))
    g.aggregator.mark_last_unread(count)
    return make_toast(200, f"Marked last {count} items as unread")
