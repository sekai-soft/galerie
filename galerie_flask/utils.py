from typing import Optional, List
from functools import wraps
from flask import request, g, redirect
from galerie.rendered_item import RenderedItem
from .get_aggregator import get_aggregator


DEFAULT_MAX_ITEMS = 10
DEFAULT_MAX_RENDERED_ITEMS = 4
cookie_max_age = 60 * 60 * 24 * 365  # 1 year


def requires_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        aggregator, _ = get_aggregator()
        if not aggregator:
            if request.path.startswith('/actions'):
                return redirect('/login')
            return redirect('/login?next=' + request.full_path)
        g.aggregator = aggregator
        return f(*args, **kwargs)
    return decorated_function


def load_more_button_args(
        args: dict,
        from_iid: str,
        gid: Optional[str],
        sort_by_desc: bool,
        infinite_scroll: bool,
        remaining_count: int,
        include_read: bool,
        total_count: int,
    ):
    args.update({
        "from_iid": from_iid,
        "gid": gid if gid is not None else "",
        "sort": "desc" if sort_by_desc else "asc",
        "infinite_scroll": infinite_scroll,
        "remaining_count": remaining_count,
        "include_read": "1" if include_read else "0",
        "total_count": total_count
    })


def items_args(args: dict, rendered_items: List[RenderedItem], should_show_feed_title: bool, should_show_feed_group: bool, no_text_mode: bool):
    rendered_feed_icons = {}
    for ri in rendered_items:
        fid = ri.fid
        if fid in rendered_feed_icons:
            continue
        rendered_feed_icons[fid] = g.aggregator.get_feed_icon(fid)

    args.update({
        "items": rendered_items,
        "should_show_feed_title": should_show_feed_title,
        "should_show_feed_group": should_show_feed_group,
        "rendered_feed_icons": rendered_feed_icons,
        "no_text_mode": no_text_mode
    })


def compute_read_percentage(remaining_count: int, total_count: int) -> int:
    if total_count == 0 or remaining_count == 0:
        return 100
    read_count = total_count - remaining_count
    return int((read_count / total_count) * 100)
