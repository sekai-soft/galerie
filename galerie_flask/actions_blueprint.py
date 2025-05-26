import os
import json
import requests
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
                return make_toast(500, str(_l("Unknown MinifluxAdminException: %(e)s", e=str(e))))
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            return make_toast(500, str(_l("Unknown server error: %(e)s", e=str(e))))
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

    resp = make_response()
    resp.headers['HX-Redirect'] = next_url
    return resp


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

    miniflux_aggregator, session_token = get_aggregator(username, password)

    resp = make_response()
    resp.set_cookie('session_token', session_token, max_age=cookie_max_age)
    resp.headers['HX-Redirect'] = next_url
    return resp


@actions_blueprint.route("/logout", methods=['POST'])
@catches_exceptions
def logout():
    if 'session_token' not in request.cookies:
        return make_toast(400, "You are not logged in")

    miniflux_admin = get_miniflux_admin()
    miniflux_admin.log_out(request.cookies['session_token'])

    resp = make_response()
    resp.delete_cookie('session_token')
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
    resp = make_response()
    resp.set_cookie('infinite_scroll', infinite_scroll, max_age=cookie_max_age)
    make_toast_header(resp, _("Setting updated"))
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


@actions_blueprint.route('/preview_feed', methods=['POST'])
@requires_auth
@catches_exceptions
def preview_feed():
    preview_group = g.aggregator.get_preview_group()
    if not preview_group:
        return make_toast(400, "Preview group is absent")
    preview_gid = preview_group.gid

    url = request.form['url']
    twitter_handle = extract_twitter_handle_from_url(url)
    if twitter_handle:
        feed_url = create_nitter_feed_url(twitter_handle)
    else:
        feed_url = url
    if not feed_url:
        return make_toast(400, "URL is required")

    fid = g.aggregator.add_feed(feed_url, preview_gid, disabled=True)
    if not fid:
        return make_toast(400, _('Unable to detect a valid feed'))
    g.aggregator.mark_all_feed_items_as_read(fid)

    resp = make_response()
    resp.headers['HX-Redirect'] = f'/preview_feed?fid={fid}'
    return resp


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


@actions_blueprint.route('/clean_up_previewed_feeds', methods=['POST'])
@requires_auth
@catches_exceptions
def clean_up_previewed_feeds():
    preview_group = g.aggregator.get_preview_group()
    g.aggregator.delete_feeds_by_group_id(preview_group.gid)

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


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

    resp = make_response()
    resp.headers['HX-Redirect'] = '/feeds?group=' + group
    return resp


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

    resp = make_response()
    resp.headers['HX-Redirect'] = '/feeds'
    return resp


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
