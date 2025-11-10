import json
from flask import request, g, Blueprint, make_response, render_template
from galerie.rendered_item import convert_rendered_items
from galerie.miniflux_aggregator import entry_dict_to_item
from galerie_flask.utils import requires_auth, load_more_button_args, items_args, DEFAULT_MAX_ITEMS, DEFAULT_MAX_RENDERED_ITEMS, compute_read_percentage
from galerie_flask.actions_blueprint import catches_exceptions
from galerie_flask.db import ItemViewHistory, Session, db


load_more_history_bp = Blueprint('load_more_history', __name__, template_folder='../../shared_templates')


@load_more_history_bp.route('/load_more_history')
@catches_exceptions
@requires_auth
def load_more_history():
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'
    max_items = int(request.cookies.get('max_items', DEFAULT_MAX_ITEMS))
    max_rendered_items = int(request.cookies.get('max_rendered_items', DEFAULT_MAX_RENDERED_ITEMS))
    no_text_mode = request.cookies.get('no_text_mode', '0') == '1'

    from_uuid = request.args.get('from_iid')  # Using from_iid param name for consistency
    remaining_count = int(request.args.get('remaining_count'))
    total_count = int(request.args.get('total_count'))
    read_percentage = compute_read_percentage(remaining_count, total_count)

    # Get user_uuid from session
    session_token = request.cookies.get('session_token')
    session = db.session.query(Session).filter_by(uuid=session_token).first()
    user_uuid = session.user_uuid

    # Get the timestamp of the last loaded item to continue pagination
    last_item = db.session.query(ItemViewHistory).filter_by(uuid=from_uuid).first()
    if not last_item:
        # If we can't find the item, return empty result
        args = {}
        rendered_string = render_template('all_loaded_marker.html', **args)
        resp = make_response(rendered_string)
        return resp

    # Query next batch of history items after the last timestamp
    view_history = db.session.query(ItemViewHistory).filter(
        ItemViewHistory.user_uuid == user_uuid,
        ItemViewHistory.created_at < last_item.created_at
    ).order_by(ItemViewHistory.created_at.desc()).limit(max_items).all()

    items = []
    for history_entry in view_history:
        try:
            if history_entry.miniflux_entry:
                item = entry_dict_to_item(history_entry.miniflux_entry)
                items.append(item)
        except Exception:
            pass

    rendered_items = convert_rendered_items(items, max_rendered_items)
    last_uuid = view_history[-1].uuid if view_history else ''

    if last_uuid:
        args = {}
        items_args(args, rendered_items, False, False, no_text_mode)
        remaining_count = remaining_count - max_items if remaining_count > max_items else 0
        load_more_button_args(
            args=args,
            from_iid=last_uuid,
            gid=None,
            sort_by_desc=True,
            infinite_scroll=infinite_scroll,
            remaining_count=remaining_count,
            include_read=False,
            total_count=total_count
        )
        rendered_string = \
            render_template('items_stream.html', **args) + "\n" + \
            render_template('load_more_button_history.html', **args)
    else:
        args = {}
        rendered_string = render_template('all_loaded_marker.html', **args)

    resp = make_response(rendered_string)
    resp.headers['HX-Trigger-After-Settle'] = json.dumps({
        "append": list(map(lambda i: i.uid, rendered_items)),
        "update_read_percentage": read_percentage
    })
    return resp
