from typing import List, Tuple, Optional
from urllib.parse import quote, quote_plus
from galerie.images import Image, uid_to_item_id
from galerie.groups import Group

I18N = {
    "zh": {
        "Galerie": "Galerie",
        "A Pinterest/Xiaohongshu photo wall style RSS reader": "一款 Pinterest/小红书照片墙式的 RSS 阅读器",
        "Logout": "登出",
        "Load COUNT more": "加载 COUNT 张更多",
        "Mark above as read": "标记以上为已读",
        "Are you sure you want to mark above as read?": "确定要标记以上为已读吗？",
        "Mark all as read": "标记全部为已读",
        "Are you sure you want to mark all as read?": "确定要标记全部为已读吗？",
        "✨ All read ✨": "✨ 全部已读 ✨",
        "✨ All GROUP_TITLE read ✨": "✨ 今日 GROUP_TITLE 图片全部已读 ✨",
        "✨ Today's images all read ✨": "✨ 今日图片全部已读 ✨",
        "✨ Today's GROUP_TITLE images all read ✨": "✨ 今日 GROUP_TITLE 图片全部已读 ✨",
        "All time": "全部",
        "Today": "今天",
        "(All groups)": "(全部分组)"
    }
}


def get_string(en_string: str, lang: str) -> str:
    return I18N.get(lang, {}).get(en_string, en_string)

GRID_ITEM_DBLCLICK_ATTRIBUTE_TEMPLATE = """ x-on:dblclick.prevent="clearTimeout(timer); fetch('/pocket?url=ENCODED_URL&TAG_ARGS', {method: 'POST'}).then(() => window.toast('Added UID to Pocket'))" """

GRID_ITEM_TEMPLATE = """<div
    class="grid-item"
    id="UID"
    x-data="{ timer: null }"
    x-on:click.prevent="clearTimeout(timer); timer = setTimeout(() => { window.open('URL', '_blank') }, 250);" GRID_ITEM_DBLCLICK_ATTRIBUTES>
    <img class="item-image" src="IMAGE_URL"/>
</div>"""

MARK_AS_READ_BUTTON_TEMPLATE = """<div
    class="button"
    style="margin-left: 4px"
    hx-confirm="MARK_AS_READ_CONFIRM"
    hx-post="/mark_as_read?session_max_uid=SESSION_MAX_UID&min_uid=MIN_UIDTODAY_PARAMGID_PARAM"
    hx-disabled-elt="this"
>MARK_AS_READ_LABEL <span class="htmx-indicator">...</span></div>"""

LOAD_MORE_BUTTONS_CONTAINER_TEMPLATE = """<div
    class="button-container stream"
    id="buttons"
    hx-swap-oob="true"
>
    <div
        class="button"
        hx-get="/load_more?session_max_uid=SESSION_MAX_UID&max_uid=MAX_UIDTODAY_PARAMGID_PARAM"
        hx-target="#grid"
        hx-swap="beforeend"
        hx-disabled-elt="this"
    >LOAD_COUNT_MORE <span class="htmx-indicator">...</span></div>
""" + MARK_AS_READ_BUTTON_TEMPLATE + """</div>"""

MARK_AS_READ_BUTTONS_TEMPLATE = """<div
    class="button-container stream"
    id="buttons"
    hx-swap-oob="true"
>""" + MARK_AS_READ_BUTTON_TEMPLATE + """</div>"""

ALL_READ_HTML_TEMPLATE = """<div class="stream">
    <p>ALL_READ_MESSAGE</p>
</div>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>COUNTGALERIE</title>
        <meta name="description" content="A_PINTEREST_XIAOHONGSHU_PHOTO_WALL_STYLE_RSS_READER">
        <link rel="icon" type="image/png" href="URL_FOR_FAVICON_PNG">
        <link rel="stylesheet" type="text/css" href="URL_FOR_STYLE_CSS">
        <script src="https://code.jquery.com/jquery-3.7.1.slim.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/masonry-layout@4.2.2/dist/masonry.pkgd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/imagesloaded@5.0.0/imagesloaded.pkgd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/htmx.org@1.9.11/dist/htmx.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.8/dist/cdn.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/js-cookie@3.0.5/dist/js.cookie.min.js"></script>
    </head>
    <body>
        <div class="stream header">
            <p>COUNTGALERIE <a href="https://github.com/sekai-soft/galerie" target="_blank" style="font-size: 1em;">&lt;/&gt;</a></p>
            <div>
                <select id="timeSelect">
                    <option value="all" TIME_OPTION_ALL_TIME_SELECT_ATTRIBUTE>TIME_OPTION_ALL_TIME</option>
                    <option value="today" TIME_OPTION_TODAY_SELECT_ATTRIBUTE>TIME_OPTION_TODAY</option>
                </select>
                <select id="groupSelect" style="width: 192px">
                    <option value="_all" GROUP_SELECT_DEFAULT_OPTION_ATTRIBUTE>GROUP_SELECT_DEFAULT_OPTION_LABEL</option>
                    GROUP_SELECT_OPTIONS
                </select>
            </div>
            <div
                class="button"
                style="visibility: LOGOUT_BUTTON_VISIBILITY"
                hx-post="/deauth"
                hx-swap="none"
            >LOGOUT</div>
        </div>
        ALL_READ
        <div class="grid stream" id="grid">
            <div class="grid-sizer"></div>
            IMAGES_HTML
        </div>
        BUTTON_HTML
        <div id="toast">Default toast message</div> 
        <script src="URL_FOR_SCRIPT_JS"></script>
    </body>
</html>
"""


def render_images_html(remaining_images: List[Image], max_images: int, double_click_action: bool) -> str:
    images = remaining_images[:max_images]
    images_html = ''
    for image in images:
        images_html += GRID_ITEM_TEMPLATE \
            .replace('UID', image.uid) \
            .replace('IMAGE_URL', image.image_url) \
            .replace('URL', image.url) \
            .replace('GRID_ITEM_DBLCLICK_ATTRIBUTES',
                     GRID_ITEM_DBLCLICK_ATTRIBUTE_TEMPLATE
                        .replace(
                            'ENCODED_URL', quote(image.url)) \
                        .replace('&TAG_ARGS', ''.join(
                            map(lambda group: f'&tag={quote_plus(group.title)}&tag={quote(f'group_id={group.gid}')}', image.groups)
                        ) if image.groups else '')
                        .replace('UID', image.uid) \
                        if double_click_action else '')
    return images_html


def render_load_more_buttons_container_html(count: int, max_uid: str, min_uid: str, session_max_uid: str, lang: str, today: bool, group_id: Optional[str]) -> str:
    # order of SESSION_MAX_UID and MAX_UID cannot be change
    # otherwise max_uid will be in SESSION_MAX_UID
    # because MAX_UID is a substring of SESSION_MAX_UID
    return LOAD_MORE_BUTTONS_CONTAINER_TEMPLATE \
        .replace('LOAD_COUNT_MORE', get_string("Load COUNT more", lang)) \
        .replace('SESSION_MAX_UID', session_max_uid) \
        .replace('MAX_UID', max_uid) \
        .replace('TODAY_PARAM', '&today=1' if today else '') \
        .replace('GID_PARAM', f'&group={group_id}' if group_id else '') \
        .replace('MIN_UID', min_uid) \
        .replace('MARK_AS_READ_CONFIRM', get_string("Are you sure you want to mark above as read?", lang)) \
        .replace('MARK_AS_READ_LABEL', get_string("Mark above as read", lang)) \
        .replace('COUNT', str(count))


def render_mark_as_read_buttons_container_html(min_uid: str, session_max_uid: str, lang: str, today: bool, group_id: Optional[str]) -> str:
    return MARK_AS_READ_BUTTONS_TEMPLATE \
        .replace('SESSION_MAX_UID', session_max_uid) \
        .replace('MIN_UID', min_uid) \
        .replace('MARK_AS_READ_CONFIRM', get_string("Are you sure you want to mark all as read?", lang)) \
        .replace('MARK_AS_READ_LABEL', get_string("Mark all as read", lang)) \
        .replace('TODAY_PARAM', '&today=1' if today else '') \
        .replace('GID_PARAM', f'&group={group_id}' if group_id else '')


def _find_last_min_uid(all_or_remaining_images: List[Image], max_images: int) -> Tuple[str, int]:
    min_uid = all_or_remaining_images[max_images - 1].uid
    item_id_for_min_uid = uid_to_item_id(min_uid)
    for index in range(max_images - 1, -1, -1):
        image = all_or_remaining_images[index]
        item_id = uid_to_item_id(image.uid)
        if item_id != item_id_for_min_uid:
            return image.uid
    return all_or_remaining_images[0].uid


def render_button_html(all_or_remaining_images: List[Image], max_images: int, session_max_uid: str, lang: str, today: bool, group_id: Optional[str]) -> str:
    if len(all_or_remaining_images) > max_images:
        count = len(all_or_remaining_images) - max_images
        max_uid = all_or_remaining_images[max_images - 1].uid
        min_uid = all_or_remaining_images[max_images].uid
        if uid_to_item_id(max_uid) != uid_to_item_id(min_uid):
            # it is possible that the image at max_imags is not the last image of the associated feed
            # if we do not find the item/image previous to this image
            # marking all items as read including this image
            # will also make the remaining images of the associated item not render at all
            # hence, we need to find the item/image previous to this image
            # and use its uid as min_uid
            min_uid = _find_last_min_uid(all_or_remaining_images, max_images)
        return render_load_more_buttons_container_html(count, max_uid, min_uid, session_max_uid, lang, today, group_id)
    else:
        min_uid = all_or_remaining_images[-1].uid
        return render_mark_as_read_buttons_container_html(min_uid, session_max_uid, lang, today, group_id)


def _all_read_message(today: bool, group: Optional[Group], lang: str):
    if today:
        if group:
            return get_string("✨ Today's GROUP_TITLE images all read ✨", lang).replace('GROUP_TITLE', group.title)
        else:
            return get_string("✨ Today's images all read ✨", lang)
    else:
        if group:
            return get_string("✨ All GROUP_TITLE read ✨", lang).replace('GROUP_TITLE', group.title)
        else:
            return get_string('✨ All read ✨', lang)
    

def render_index(
        all_images: List[Image],
        max_images: int,
        url_for_style_css: str,
        url_for_favicon_png: str,
        url_for_script_js: str,
        double_click_action: bool,
        has_auth_cookie: bool,
        lang: str,
        today: bool,
        all_groups: List[Group],
        selected_group: Optional[Group]) -> str:
    images_html = render_images_html(all_images, max_images, double_click_action)
    if all_images:
        button_html = render_button_html(all_images, max_images, all_images[0].uid, lang, today, selected_group.gid if selected_group else None)
    else:
        button_html = ''
    nothing_left = not all_images
    return INDEX_TEMPLATE \
        .replace('GALERIE', get_string('Galerie', lang)) \
        .replace('A_PINTEREST_XIAOHONGSHU_PHOTO_WALL_STYLE_RSS_READER', get_string('A Pinterest/Xiaohongshu photo wall style RSS reader', lang)) \
        .replace('COUNT', f'({len(all_images)}) ' if not nothing_left else '') \
        .replace('TIME_OPTION_ALL_TIME_SELECT_ATTRIBUTE', 'selected="selected"' if not today else '') \
        .replace('TIME_OPTION_ALL_TIME', get_string('All time', lang)) \
        .replace('TIME_OPTION_TODAY_SELECT_ATTRIBUTE', 'selected="selected"' if today else '') \
        .replace('TIME_OPTION_TODAY', get_string('Today', lang)) \
        .replace('GROUP_SELECT_DEFAULT_OPTION_LABEL', get_string('(All groups)', lang)) \
        .replace('GROUP_SELECT_DEFAULT_OPTION_ATTRIBUTE', 'selected="selected"' if not selected_group else '') \
        .replace('GROUP_SELECT_OPTIONS', ''.join(map(
            lambda g: f'<option value="{g.gid}" {'selected="selected"' if selected_group and g.gid == selected_group.gid else ''}>{g.title}</option>', all_groups
        ))) \
        .replace('LOGOUT_BUTTON_VISIBILITY', 'visible' if has_auth_cookie else 'hidden') \
        .replace('LOGOUT', get_string('Logout', lang)) \
        .replace('ALL_READ', ALL_READ_HTML_TEMPLATE.replace(
            'ALL_READ_MESSAGE',
            _all_read_message(today, selected_group, lang) if nothing_left else '')) \
        .replace('IMAGES_HTML', images_html) \
        .replace('BUTTON_HTML', button_html) \
        .replace('URL_FOR_STYLE_CSS', url_for_style_css) \
        .replace('URL_FOR_FAVICON_PNG', url_for_favicon_png) \
        .replace('URL_FOR_SCRIPT_JS', url_for_script_js)