import os
import json
from typing import Dict
from functools import wraps
from flask import request, g, Blueprint, make_response, Response
from flask_babel import _
from sentry_sdk import capture_exception
from .utils import requires_auth, cookie_max_age
from .get_aggregator import get_aggregator
from .miniflux_admin import get_miniflux_admin, MinifluxAdminException


actions_blueprint = Blueprint('actions_legacy', __name__)


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
            if not e.expected:
                if os.getenv('DEBUG', '0') == '1':
                    raise e
                capture_exception(e)
            return make_toast(e.status_code, e.human_readable_message)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            return make_toast(500, f"Unknown server error: {str(e)}")
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


@actions_blueprint.route('/set_infinite_scroll', methods=['POST'])
@catches_exceptions
def set_infinite_scroll():
    infinite_scroll = request.form.get('infinite_scroll', '0')

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
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


@actions_blueprint.route('/delete_feed', methods=['POST'])
@requires_auth
@catches_exceptions
def delete_feed():
    if 'fid' not in request.args:
        return make_toast(400, "Feed is required")
    fid = request.args.get('fid')

    g.aggregator.delete_feed(fid)

    return make_back()


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


@actions_blueprint.route('/refresh_all_dead_feeds', methods=['POST'])
@requires_auth
@catches_exceptions
def refresh_all_dead_feeds():
    total_count = 0
    success_count = 0

    for feed in g.aggregator.client.get_feeds():
        if feed.get("parsing_error_count", 0) == 0:
            continue

        try:
            g.aggregator.client.refresh_feed(feed["id"])
            success_count += 1
        except Exception as e:
            pass
        total_count += 1

    resp = make_response()
    resp.headers['HX-Refresh'] = "true"
    return resp


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
