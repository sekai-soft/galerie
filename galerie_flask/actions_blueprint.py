import os
import json
import requests
from typing import Dict
from functools import wraps
from urllib.parse import unquote
from flask import request, g, Blueprint, make_response, render_template, Response
from flask_babel import _, lazy_gettext as _l
from sentry_sdk import capture_exception
from requests.auth import HTTPBasicAuth
from galerie.feed_filter import FeedFilter
from galerie.rendered_item import convert_rendered_items
from galerie.twitter import create_nitter_feed_url, extract_twitter_handle_from_url
from .utils import requires_auth, max_items, load_more_button_args, mark_as_read_button_args, items_args, add_image_ui_extras, \
    cookie_max_age
from .get_aggregator import get_aggregator
from .miniflux_admin import get_miniflux_admin, MinifluxAdminException, MinifluxAdminErrorCode
from .instapaper import get_instapaper_auth, is_instapaper_available
from .instapaper_manager import get_instapaper_manager


actions_blueprint = Blueprint('actions', __name__)


def make_hx_trigger_header(resp: Response, trigger_message: Dict):
    resp.headers['HX-Trigger'] = json.dumps(trigger_message)


def make_toast(status_code: int, message: str):
    resp = make_response()
    make_hx_trigger_header(resp, {
        "toast": message
    })
    resp.status_code = status_code
    return resp


def make_back(status_code: int=200):
    resp = make_response()
    make_hx_trigger_header(resp, {
        "back": True
    })
    resp.status_code = status_code
    return resp


def make_hx_redirect(url: str):
    resp = make_response()
    resp.headers['HX-Redirect'] = url
    return resp


def catches_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except MinifluxAdminException as e:
            if e.error_code == MinifluxAdminErrorCode.USERNAME_ALREADY_EXISTS:
                return make_toast(400, _("Username already exists"))
            elif e.error_code == MinifluxAdminErrorCode.WRONG_CREDENTIALS:
                return make_toast(400, _("Wrong credentials"))
            elif e.error_code == MinifluxAdminErrorCode.LOGGED_OUT:
                return make_toast(401, "Logged out")
            elif e.error_code == MinifluxAdminErrorCode.ABSENT_USER:
                return make_toast(404, "User not found")
            elif e.error_code == MinifluxAdminErrorCode.SESSION_EXPIRED:
                return make_toast(401, _("Your session has expired"))
            else:
                return make_toast(500, f"Unknown MinifluxAdminException: {str(e)}")
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            return make_toast(500, f"Unknown server error: str(e)")
    return decorated_function


@actions_blueprint.route('/signup', methods=['POST'])
@catches_exceptions
def signup():
    next_url = request.args.get('next', '/')

    username = request.form.get('username', '')
    if not username:
        return make_toast(400, _("Username is required"))

    password = request.form.get('password', '')
    if not password:
        return make_toast(400, _("Password is required"))

    repeat_password = request.form.get('repeat_password', '')
    if not repeat_password:
        return make_toast(400, _("Password is required"))

    if password != repeat_password:
        return make_toast(400, _("Passwords do not match"))

    miniflux_admin = get_miniflux_admin()
    miniflux_admin.sign_up(username, password)

    return make_hx_redirect(next_url)


@actions_blueprint.route('/login', methods=['POST'])
@catches_exceptions
def login():
    next_url = request.args.get('next', '/')

    username = request.form.get('username', '')
    if not username:
        return make_toast(400, _("Username is required"))

    password = request.form.get('password', '')
    if not password:
        return make_toast(400, _("Password is required"))

    session_token = get_aggregator(username, password)[1]

    resp = make_hx_redirect(next_url)
    resp.set_cookie('session_token', session_token, max_age=cookie_max_age)
    return resp


@actions_blueprint.route("/logout", methods=['POST'])
@catches_exceptions
def logout():
    if 'session_token' not in request.cookies:
        return make_toast(400, "You are not logged in")

    miniflux_admin = get_miniflux_admin()
    miniflux_admin.log_out(request.cookies['session_token'])

    resp = make_hx_redirect('/login')
    resp.delete_cookie('session_token')
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
        items_args(args, rendered_items, True, gid is None)
        remaining_count = remaining_count - max_items if remaining_count > max_items else 0
        load_more_button_args(args, last_iid, gid, sort_by, infinite_scroll, remaining_count)
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


@actions_blueprint.route('/set_infinite_scroll', methods=['POST'])
@catches_exceptions
def set_infinite_scroll():
    infinite_scroll = request.form.get('infinite_scroll', '0')

    resp = make_toast(200, _("Setting updated"))
    resp.set_cookie('infinite_scroll', infinite_scroll, max_age=cookie_max_age)
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

    enable = request.args.get('enable', '0') == '1'
    if enable:
        g.aggregator.enable_feed(fid)

    return make_toast(200, str(_("Group updated")))


@actions_blueprint.route('/add_feed', methods=['POST'])
@requires_auth
@catches_exceptions
def add_feed():
    if 'group' not in request.form:
        return make_toast(400, "Group is required")
    gid = request.form.get('group')

    view_feed = request.args.get('view_feed', '0') == '1'

    def make_response(fid: str):
        if view_feed:
            return make_hx_redirect(f'/feed?fid={fid}')
        return make_back()

    url = request.form['url']
    existing_fid = g.aggregator.find_feed_by_feed_url(url)
    if existing_fid:
        return make_response(existing_fid)

    twitter_handle = extract_twitter_handle_from_url(url)
    if twitter_handle:
        feed_url = create_nitter_feed_url(twitter_handle)
    else:
        feed_url = url
    if not feed_url:
        return make_toast(400, "URL is required")

    fid = g.aggregator.add_feed(feed_url, gid)
    if not fid:
        return make_toast(400, _('Unable to detect a valid feed'))

    return make_response(fid)


@actions_blueprint.route('/delete_feed', methods=['POST'])
@requires_auth
@catches_exceptions
def delete_feed():
    if 'fid' not in request.args:
        return make_toast(400, "Feed is required")
    fid = request.args.get('fid')

    g.aggregator.delete_feed(fid)

    return make_back()


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
        return make_toast(400, _("Wrong Instapaper credentials"))
    
    instapaper_manager = get_instapaper_manager()
    instapaper_manager.add_instapaper_connection(
        session_token=request.cookies.get('session_token'),
        instapaper_username=username_or_email,
        instapaper_password=password
    )

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/log_out_of_instapaper', methods=['POST'])
@catches_exceptions
def log_out_of_instapaper():
    instapaper_manager = get_instapaper_manager()
    instapaper_manager.remove_instapaper_connection(
        request.cookies.get('session_token'),
    )

    resp = make_response()
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


@actions_blueprint.route('/rename_group', methods=['POST'])
@requires_auth
@catches_exceptions
def rename_group():
    group = request.args.get('group')
    if group is None:
        return make_toast(400, "Group is required")

    name = request.form.get('name')
    if name is None:
        return make_toast(400, "Name is required")
    
    g.aggregator.rename_group(group, name)

    return make_back()


@actions_blueprint.route('/delete_group', methods=['POST'])
@requires_auth
@catches_exceptions
def delete_group():
    group = request.args.get('group')
    if group is None:
        return make_toast(400, "Group is required")
    
    if len(g.aggregator.get_groups()) == 1:
        return make_toast(400, _("You cannot delete the last group"))

    g.aggregator.delete_group(group)

    return make_back()


@actions_blueprint.route('/delete_feeds', methods=['POST'])
@requires_auth
@catches_exceptions
def delete_feeds():
    for item in request.form:
        if item.startswith('dead-feed-'):
            fid = item[len("dead-feed-"):]
            g.aggregator.delete_feed(fid)

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/clean_up_duplicated_twitter_feeds', methods=['POST'])
@requires_auth
@catches_exceptions
def clean_up_duplicated_twitter_feeds():
    feeds = g.aggregator.get_feeds()

    maybe_duplicated_twitter_feeds = {}
    for feed in feeds:
        if feed.features.get('twitter_handle'):
            twitter_handle = feed.features['twitter_handle'].lower()
            if twitter_handle not in maybe_duplicated_twitter_feeds:
                maybe_duplicated_twitter_feeds[twitter_handle] = []
            maybe_duplicated_twitter_feeds[twitter_handle].append(feed.fid)

    for twitter_handle, feed_fids in maybe_duplicated_twitter_feeds.items():
        if len(feed_fids) > 1:
            feed_fids = sorted(feed_fids, key=lambda fid: int(fid), reverse=True) # todo: miniflux hack that ensures we only keep the newest feed
            for fid in feed_fids[1:]:
                g.aggregator.delete_feed(fid)

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


@actions_blueprint.route('/create_group', methods=['POST'])
@requires_auth
@catches_exceptions
def create_group():
    name = request.form.get('name')
    if not name:
        return make_toast(400, _("Name is required"))

    g.aggregator.create_group(name)

    return make_back()


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
