import json
from flask import request, g, Blueprint, make_response, render_template
from galerie.rendered_item import convert_rendered_items
from galerie_flask.utils import requires_auth, load_more_button_args, items_args, DEFAULT_MAX_ITEMS, DEFAULT_MAX_RENDERED_ITEMS, compute_read_percentage
from galerie_flask.actions_blueprint import catches_exceptions


load_more_bp = Blueprint('load_more', __name__, template_folder='../../shared_templates')


@load_more_bp.route('/load_more')
@catches_exceptions
@requires_auth
def load_more():
    sort_by_desc = request.args.get('sort', 'desc') == 'desc'
    gid = request.args.get('group') if request.args.get('group') else None
    include_read = request.args.get('read', '0') == '1'
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    max_items = int(request.cookies.get('max_items', DEFAULT_MAX_ITEMS))
    max_rendered_items = int(request.cookies.get('max_rendered_items', DEFAULT_MAX_RENDERED_ITEMS))
    no_text_mode = request.cookies.get('no_text_mode', '0') == '1'

    from_iid = request.args.get('from_iid')
    remaining_count = int(request.args.get('remaining_count'))
    total_count = int(request.args.get('total_count'))
    read_percentage = compute_read_percentage(remaining_count, total_count)

    # Get after, before, and section_id from query parameters
    after_str = request.args.get('after', '')
    after = int(after_str) if after_str else None
    before_str = request.args.get('before', '')
    before = int(before_str) if before_str else None
    section_id = request.args.get('section_id', '')

    unread_items = g.aggregator.get_items(
        count=max_items,
        from_iid_exclusive=from_iid,
        group_id=gid,
        sort_by_id_descending=sort_by_desc,
        include_read=include_read,
        after=after,
        before=before
    )

    rendered_items = convert_rendered_items(unread_items, max_rendered_items)
    last_iid = unread_items[-1].iid if unread_items else ''

    if last_iid:
        args = {}
        items_args(args, rendered_items, True, gid is None, no_text_mode)
        remaining_count = remaining_count - max_items if remaining_count > max_items else 0
        load_more_button_args(
            args=args,
            from_iid=last_iid,
            gid=gid,
            sort_by_desc=sort_by_desc,
            infinite_scroll=infinite_scroll,
            remaining_count=remaining_count,
            include_read=include_read,
            total_count=total_count,
            after=after,
            before=before
        )
        args['section_id'] = section_id
        rendered_string = \
            render_template('items_stream.html', **args) + "\n" + \
            render_template('load_more_button.html', **args)
    else:
        args = {}
        rendered_string = render_template('all_loaded_marker.html', **args)

    resp = make_response(rendered_string)
    resp.headers['HX-Trigger-After-Settle'] = json.dumps({
        "append": list(map(lambda i: i.uid, rendered_items)),
        "update_read_percentage": read_percentage
    })
    return resp
