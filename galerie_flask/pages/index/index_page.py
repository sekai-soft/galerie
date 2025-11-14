from flask import Blueprint, render_template, g, request
from flask_babel import _
from datetime import datetime, timedelta
from galerie.rendered_item import convert_rendered_items
from galerie_flask.utils import requires_auth, items_args, load_more_button_args, DEFAULT_MAX_ITEMS, DEFAULT_MAX_RENDERED_ITEMS, compute_read_percentage
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

    # Calculate timestamps for three sections
    now = datetime.now()
    time_24h_ago = int((now - timedelta(hours=24)).timestamp())
    time_48h_ago = int((now - timedelta(hours=48)).timestamp())

    # Fetch items for each section
    # Section 1: Past 24 hours (published >= 24h ago)
    section_24h_items = g.aggregator.get_items(
        count=max_items,
        from_iid_exclusive=None,
        group_id=gid,
        sort_by_id_descending=sort_by_desc,
        include_read=include_read,
        after=time_24h_ago
    )

    # Section 2: 24-48 hours (48h ago <= published < 24h ago)
    section_24_48h_items = g.aggregator.get_items(
        count=max_items,
        from_iid_exclusive=None,
        group_id=gid,
        sort_by_id_descending=sort_by_desc,
        include_read=include_read,
        after=time_48h_ago,
        before=time_24h_ago
    )

    # Section 3: Beyond 48 hours (published < 48h ago)
    section_beyond_48h_items = g.aggregator.get_items(
        count=max_items,
        from_iid_exclusive=None,
        group_id=gid,
        sort_by_id_descending=sort_by_desc,
        include_read=include_read,
        before=time_48h_ago
    )

    # Convert to rendered items for each section
    rendered_24h = convert_rendered_items(section_24h_items, max_rendered_items)
    rendered_24_48h = convert_rendered_items(section_24_48h_items, max_rendered_items)
    rendered_beyond_48h = convert_rendered_items(section_beyond_48h_items, max_rendered_items)

    # Get last item IDs for pagination
    last_iid_24h = section_24h_items[-1].iid if section_24h_items else ''
    last_iid_24_48h = section_24_48h_items[-1].iid if section_24_48h_items else ''
    last_iid_beyond_48h = section_beyond_48h_items[-1].iid if section_beyond_48h_items else ''

    groups = g.aggregator.get_groups()
    gids = [group.gid for group in groups]
    all_group_counts = g.aggregator.get_unread_items_count_by_group_ids(gids, include_read)
    all_unread_count = sum(all_group_counts.values())
    groups = sorted(groups, key=lambda group: all_group_counts[group.gid], reverse=True)
    selected_group = next((group for group in groups if group.gid == gid), None)

    total_count = all_group_counts[gid] if gid is not None else all_unread_count
    # For read percentage, use the total of all sections
    total_items_shown = len(section_24h_items) + len(section_24_48h_items) + len(section_beyond_48h_items)
    remaining_count = total_count - total_items_shown if total_count > total_items_shown else 0
    read_percentage = compute_read_percentage(remaining_count, total_count)

    all_feed_count = sum(group.feed_count for group in groups)
    feeds = g.aggregator.get_feeds()

    # Prepare arguments for each section
    args_24h = {}
    items_args(args_24h, rendered_24h, True, gid is None, no_text_mode)
    load_more_button_args(
        args=args_24h,
        from_iid=last_iid_24h,
        gid=gid,
        sort_by_desc=sort_by_desc,
        infinite_scroll=infinite_scroll,
        remaining_count=0,  # Will be calculated dynamically
        include_read=include_read,
        total_count=len(section_24h_items),
        after=time_24h_ago
    )

    args_24_48h = {}
    items_args(args_24_48h, rendered_24_48h, True, gid is None, no_text_mode)
    load_more_button_args(
        args=args_24_48h,
        from_iid=last_iid_24_48h,
        gid=gid,
        sort_by_desc=sort_by_desc,
        infinite_scroll=infinite_scroll,
        remaining_count=0,  # Will be calculated dynamically
        include_read=include_read,
        total_count=len(section_24_48h_items),
        after=time_48h_ago,
        before=time_24h_ago
    )

    args_beyond_48h = {}
    items_args(args_beyond_48h, rendered_beyond_48h, True, gid is None, no_text_mode)
    load_more_button_args(
        args=args_beyond_48h,
        from_iid=last_iid_beyond_48h,
        gid=gid,
        sort_by_desc=sort_by_desc,
        infinite_scroll=infinite_scroll,
        remaining_count=0,  # Will be calculated dynamically
        include_read=include_read,
        total_count=len(section_beyond_48h_items),
        before=time_48h_ago
    )

    args = {
        "groups": groups,
        "all_group_counts": all_group_counts,
        "all_unread_count": all_unread_count,
        "selected_group": selected_group,
        "sort_by_desc": sort_by_desc,
        "all_feed_count": all_feed_count,
        "feeds": feeds,
        "no_text_mode": no_text_mode,
        "read_percentage": read_percentage,
        "section_24h": args_24h,
        "section_24_48h": args_24_48h,
        "section_beyond_48h": args_beyond_48h,
        "has_24h_items": len(section_24h_items) > 0,
        "has_24_48h_items": len(section_24_48h_items) > 0,
        "has_beyond_48h_items": len(section_beyond_48h_items) > 0,
        "last_iid_24h": last_iid_24h,
        "last_iid_24_48h": last_iid_24_48h,
        "last_iid_beyond_48h": last_iid_beyond_48h,
    }

    return render_template('index.html', **args)
