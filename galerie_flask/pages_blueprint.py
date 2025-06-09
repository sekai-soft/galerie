import os
from functools import wraps
from urllib.parse import urlparse
from sentry_sdk import capture_exception
from flask import Blueprint, redirect, render_template, g, request, jsonify, make_response
from flask_babel import _
from galerie.rendered_item import convert_rendered_items
from galerie.utils import get_base_url
from .utils import requires_auth, max_items, load_more_button_args, items_args
from .get_aggregator import get_aggregator
from .instapaper import get_instapaper_auth, is_instapaper_available
from .miniflux_admin import MinifluxAdminException


pages_blueprint = Blueprint('pages_legacy', __name__, static_folder='static', template_folder='templates')


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
            return render_template('error.html', error=e.human_readable_message)
        except Exception as e:
            if os.getenv('DEBUG', '0') == '1':
                raise e
            capture_exception(e)
            return render_template('error.html', error=str(e))
    return decorated_function


def no_cache(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        response = make_response(view_function(*args, **kwargs))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return decorated_function


@pages_blueprint.route("/manifest.json")
def pwa_manifest():
    return jsonify({
        "theme_color": "#1a1a1a",
        "background_color": "#1a1a1a",
        "icons": [
            {
                "purpose": "maskable",
                "sizes": "512x512",
                "src": "icon512_maskable.png",
                "type": "image/png"
            },
            {
                "purpose": "any",
                "sizes": "512x512",
                "src": "icon512_rounded.png",
                "type": "image/png"
            }
        ],
        "orientation": "any",
        "display": "standalone",
        "dir": "auto",
        "lang": "en-US",
        "name": "Galerie",
        "short_name": "Galerie",
        "start_url": get_base_url(),
        "share_target": {
            "action": "add_feed",
            "method": "GET",
            "params": {
                "title": "title",
                "text": "text",
                "url": "url"
            }
        }
    })


@pages_blueprint.route("/login")
@catches_exceptions
def login_page():
    aggregator, _ = get_aggregator()
    if aggregator:
        return redirect('/')
    next_url = request.args.get('next', '/')
    return render_template('login.html', next_url=next_url)


@pages_blueprint.route("/signup")
@catches_exceptions
def signup_page():
    next_url = request.args.get('next', '/')
    return render_template('signup.html', next_url=next_url)


@pages_blueprint.route("/")
@catches_exceptions
@requires_auth
def index_page():
    sort_by_desc = request.args.get('sort', 'desc') == 'desc'
    gid = request.args.get('group') if request.args.get('group') else None
    include_read = request.args.get('read', '0') == '1'
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'

    unread_items = g.aggregator.get_items(
        count=max_items,
        from_iid_exclusive=None,
        group_id=gid,
        sort_by_id_descending=sort_by_desc,
        include_read=include_read
    )

    rendered_items = convert_rendered_items(unread_items)
    last_iid = unread_items[-1].iid if unread_items else ''

    groups = g.aggregator.get_groups()
    gids = [group.gid for group in groups]
    all_group_counts = g.aggregator.get_unread_items_count_by_group_ids(gids, include_read)
    all_unread_count = sum(all_group_counts.values())
    groups = sorted(groups, key=lambda group: all_group_counts[group.gid], reverse=True)   
    selected_group = next((group for group in groups if group.gid == gid), None)
    remaining_count = (all_group_counts[gid] if gid is not None else all_unread_count)
    remaining_count = remaining_count - max_items if remaining_count > max_items else 0
    all_feed_count = sum(group.feed_count for group in groups)
    feeds = g.aggregator.get_feeds()

    args = {
        "groups": groups,
        "all_group_counts": all_group_counts,
        "all_unread_count": all_unread_count,
        "selected_group": selected_group,
        "sort_by_desc": sort_by_desc,
        "last_iid": last_iid,
        "all_feed_count": all_feed_count,
        "feeds": feeds,
    }
    items_args(args, rendered_items, True, gid is None)
    
    load_more_button_args(
        args=args,
        from_iid=last_iid,
        gid=gid,
        sort_by_desc=sort_by_desc,
        infinite_scroll=infinite_scroll,
        remaining_count=remaining_count,
        include_read=include_read
    )

    return render_template('index.html', **args)


@pages_blueprint.route("/settings")
@catches_exceptions
@requires_auth
def settings_page():
    connection_info = g.aggregator.connection_info()
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    instapaper_available = is_instapaper_available()
    instapaper_auth = None
    if instapaper_available:
        instapaper_auth = get_instapaper_auth()
    username = g.aggregator.get_username()
    
    return render_template(
        'settings.html',
        connection_info=connection_info,
        infinite_scroll=infinite_scroll,
        is_instapaper_available=instapaper_available,
        instapaper_auth=instapaper_auth,
        username=username,
    )


@pages_blueprint.route("/manage_feeds")
@catches_exceptions
@requires_auth
@no_cache
def manage_feeds_page():
    groups = g.aggregator.get_groups()
    if not groups:
        raise ValueError("No groups found")
    groups = sorted(groups, key=lambda group: group.feed_count, reverse=True)

    gid = request.args.get('group')
    if gid is None:
        return redirect(f'/manage_feeds?group={groups[0].gid}')
    
    feeds = g.aggregator.get_feeds_by_group_id(gid)
    feeds = sorted(feeds, key=lambda feed: (0 if feed.error else 1, feed.title))

    feed_counts = {}
    for group in groups:
        feed_counts[group.gid] = group.feed_count

    return render_template(
        'manage_feeds.html',
        groups=groups,
        gid=gid,
        feeds=feeds,
        feed_counts=feed_counts,
    )


@pages_blueprint.route("/update_feed")
@catches_exceptions
@requires_auth
def update_feed_page():
    fid = request.args.get('fid')

    args = {
        "feed": g.aggregator.get_feed(fid),
        "groups": g.aggregator.get_groups(),
    }
    return render_template('update_feed.html', **args)


def is_valid_url(url: str) -> bool:
    try:
        urlparse(url)
        return True
    except ValueError:
        return False


bookmarklet = f"""javascript:(function() {{
  const url = `{get_base_url()}/add_feed?url=${{window.location.href}}&view_feed=1`;
  window.open(url, '_blank').focus();
}})();
"""

@pages_blueprint.route("/add_feed")
@catches_exceptions
@requires_auth
def add_feed_page():   
    args = request.args
    url = None
    if 'url' in args and is_valid_url(args['url']):
        url = args['url']
    elif 'text' in args and is_valid_url(args['text']):
        url = args['text']
    elif 'title' in args and is_valid_url(args['title']):
        url = args['title']

    add_feed_behavior = ''
    if args.get('view_feed', '0')== '1':
        add_feed_behavior += '?view_feed=1'
    if args.get('go_home', '0')== '1':
        add_feed_behavior += '?go_home=1'

    default_group = args.get('group')

    return render_template(
        'add_feed.html',
        url=url,
        bookmarklet=bookmarklet,
        groups=g.aggregator.get_groups(),
        add_feed_behavior=add_feed_behavior,
        default_group=default_group
    )


@pages_blueprint.route("/update_group")
@catches_exceptions
@requires_auth
def update_group_page():
    gid = request.args.get('group')

    return render_template(
        'update_group.html',
        group=g.aggregator.get_group(gid),
    )


@pages_blueprint.route("/manage_groups")
@catches_exceptions
@requires_auth
@no_cache
def manage_groups_page():
    groups = g.aggregator.get_groups()
    if not groups:
        raise ValueError("No groups found")
    groups = sorted(groups, key=lambda group: group.gid, reverse=True)

    return render_template(
        'manage_groups.html',
        groups=groups,
    )


@pages_blueprint.route("/add_group")
@catches_exceptions
@requires_auth
def add_group_page():
    return render_template('add_group.html')


@pages_blueprint.route("/debug")
@catches_exceptions
@requires_auth
def debug_page():
    return render_template('debug.html')
