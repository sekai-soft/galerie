import json
from typing import Optional, List, Tuple
from functools import wraps
from urllib.parse import quote, quote_plus
from flask import request, g, redirect, Response
from flask_babel import _
from galerie.rendered_item import RenderedItem
from galerie.twitter import fix_shareable_twitter_url
from .get_aggregator import get_aggregator

max_items = 10
cookie_max_age = 60 * 60 * 24 * 365  # 1 year


def get_instapaper_auth() -> Tuple[str, str]:
    if 'instapaper_auth' in request.cookies:
        instapaper_auth = json.loads(request.cookies['instapaper_auth'])
        return instapaper_auth['username_or_email'], instapaper_auth['password']
    return None, None


def is_instapaper_available():
    return 'instapaper_auth' in request.cookies


def requires_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        aggregator = get_aggregator()
        if not aggregator:
            if request.path.startswith('/actions'):
                return redirect('/login')
            return redirect('/login?next=' + request.full_path)
        g.aggregator = aggregator
        return f(*args, **kwargs)
    return decorated_function


def load_more_button_args(args: dict, from_iid: str, gid: Optional[str], sort_by_desc: bool, infinite_scroll: bool, remaining_count: int = 0):
    args.update({
        "from_iid": from_iid,
        "gid": gid if gid is not None else "",
        "sort": "desc" if sort_by_desc else "asc",
        "infinite_scroll": infinite_scroll,
        "remaining_count": remaining_count
    })


def mark_as_read_button_args(args: dict, gid: Optional[str], sort_by_desc: bool):
    args.update({
        "gid": gid if gid is not None else "",
        "sort": "desc" if sort_by_desc else "asc"
    })


def items_args(args: dict, rendered_items: List[RenderedItem], should_show_feed_title: bool, should_show_feed_group: bool):
    args.update({
        "items": rendered_items,
        "should_show_feed_title": should_show_feed_title,
        "should_show_feed_group": should_show_feed_group,
    })


def add_image_ui_extras(rendered_item: RenderedItem):
    rendered_item.ui_extra['quoted_url'] = quote(rendered_item.url)
    rendered_item.ui_extra['encoded_tags'] = ''.join(map(
        lambda g: f'&tag={quote_plus(g.title)}&tag={quote(f'group_id={g.gid}')}', rendered_item.groups)) if rendered_item.groups else ''
    rendered_item.ui_extra['shareable_url'] = fix_shareable_twitter_url(rendered_item.url)


def encode_setup_from_cookies() -> str:
    data = {
        'auth': request.cookies['auth']
    }

    if 'infinite_scroll' in request.cookies:
        data['infinite_scroll'] = request.cookies['infinite_scroll']
    if 'instapaper_auth' in request.cookies:
        data['instapaper_auth'] = request.cookies['instapaper_auth']

    return json.dumps(data)


def decode_setup_to_cookies(setup_code: str, response: Response):
    setup = json.loads(setup_code)
    response.set_cookie('auth', setup['auth'], max_age=cookie_max_age)

    if 'infinite_scroll' in setup:
        response.set_cookie('infinite_scroll', setup['infinite_scroll'], max_age=cookie_max_age)
    if 'instapaper_auth' in setup:
        response.set_cookie('instapaper_auth', setup['instapaper_auth'], max_age=cookie_max_age)

    return response
