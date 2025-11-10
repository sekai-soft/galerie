from flask import Blueprint, render_template, request
from flask_babel import _
from galerie.rendered_item import convert_rendered_items
from galerie.miniflux_aggregator import entry_dict_to_item
from galerie_flask.utils import requires_auth, items_args, load_more_button_args, DEFAULT_MAX_ITEMS, DEFAULT_MAX_RENDERED_ITEMS, compute_read_percentage
from galerie_flask.pages_blueprint import catches_exceptions, requires_auth
from galerie_flask.db import ItemViewHistory, Session, db


item_history_bp = Blueprint('item_history', __name__, template_folder='.')


@item_history_bp.route("/history")
@catches_exceptions
@requires_auth
def item_history_page():
    max_items = int(request.cookies.get('max_items', DEFAULT_MAX_ITEMS))
    max_rendered_items = int(request.cookies.get('max_rendered_items', DEFAULT_MAX_RENDERED_ITEMS))
    no_text_mode = request.cookies.get('no_text_mode', '0') == '1'
    infinite_scroll = request.cookies.get('infinite_scroll', '1') == '1'

    # Get user_uuid from session
    session_token = request.cookies.get('session_token')
    session = db.session.query(Session).filter_by(uuid=session_token).first()
    user_uuid = session.user_uuid

    # Count total history items
    total_count = db.session.query(ItemViewHistory).filter_by(
        user_uuid=user_uuid
    ).count()

    # Query item view history for the current user, ordered by most recent first, limited
    view_history = db.session.query(ItemViewHistory).filter_by(
        user_uuid=user_uuid
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

    args = {
        "context_history_page": True,
        "has_history": total_count > 0,
    }
    items_args(args, rendered_items, False, False, no_text_mode)

    # Add load more button if there are more items
    remaining_count = total_count - max_items
    if view_history and remaining_count > 0:
        last_uuid = view_history[-1].uuid
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
        args["show_load_more"] = True
    else:
        args["show_load_more"] = False

    return render_template('item_history.html', **args)
