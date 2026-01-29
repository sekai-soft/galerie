from flask import Blueprint, render_template, g, request
from flask_babel import _
from galerie.rendered_item import convert_rendered_items
from galerie_flask.utils import (
    requires_auth,
    items_args,
    load_more_button_args,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MAX_RENDERED_ITEMS,
    compute_read_percentage,
)
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth


index_bp = Blueprint('index', __name__, template_folder='.')


@index_bp.route("/")
@catches_exceptions
@requires_auth
def index_page():
    sort_by_desc = request.args.get('sort', 'desc') == 'desc'
    gid = request.args.get('group') if request.args.get('group') else None
    include_read = request.args.get('read', '0') == '1'
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    max_items = int(request.cookies.get('max_items', DEFAULT_MAX_ITEMS))
    max_rendered_items = int(request.cookies.get('max_rendered_items', DEFAULT_MAX_RENDERED_ITEMS))
    no_text_mode = request.cookies.get('no_text_mode', '0') == '1'

    unread_items = g.aggregator.get_items(
        count=max_items,
        from_iid_exclusive=None,
        group_id=gid,
        sort_by_id_descending=sort_by_desc,
        include_read=include_read
    )

    rendered_items = convert_rendered_items(unread_items, max_rendered_items)
    last_iid = unread_items[-1].iid if unread_items else ''

    groups = g.aggregator.get_groups()
    gids = [group.gid for group in groups]
    all_group_counts = g.aggregator.get_unread_items_count_by_group_ids(gids, include_read)
    all_unread_count = sum(all_group_counts.values())
    groups = sorted(groups, key=lambda group: all_group_counts[group.gid], reverse=True)   
    selected_group = next((group for group in groups if group.gid == gid), None)

    total_count = all_group_counts[gid] if gid is not None else all_unread_count
    remaining_count = total_count - max_items if total_count > max_items else 0
    read_percentage = compute_read_percentage(remaining_count, total_count)
    
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
        "no_text_mode": no_text_mode,
        "read_percentage": read_percentage,
    }
    items_args(args, rendered_items, True, gid is None, no_text_mode)
    load_more_button_args(
        args=args,
        from_iid=last_iid,
        gid=gid,
        sort_by_desc=sort_by_desc,
        infinite_scroll=infinite_scroll,
        remaining_count=remaining_count,
        include_read=include_read,
        total_count=total_count,
    )

    return render_template('index.html', **args)
