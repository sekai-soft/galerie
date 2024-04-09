from typing import List
from rss_waterfall.images import Image


GRID_ITEM_TEMPLATE = """<div class="grid-item" id="UID" x-data="{}" x-on:click="window.open('URL', '_blank')">
    <img class="item-image" src="IMAGE_URL"/>
</div>"""

MOTTO_BUTTON_TEMPLATE = """<div
    id="motto"
    class="tag"
    hx-swap-oob="true"
    hx-get="/motto?max_uid=MAX_UID"
    hx-target="#grid"
    hx-swap="beforeend"
>もっと</div>"""

OWARI_BUTTON = """<div
    id="motto"
    class="tag"
    hx-swap-oob="true"
>終わり</div>"""

INDEX_TEMPLATE = f"""<!DOCTYPE html>
<html>
    <head>
        <title>(COUNT) RSS Waterfall</title>
        <link rel="stylesheet" type="text/css" href="URL_FOR_STYLE_CSS">
        <script src="https://code.jquery.com/jquery-3.7.1.slim.js"></script>
        <script src="https://unpkg.com/masonry-layout@4/dist/masonry.pkgd.js"></script>
        <script src="https://unpkg.com/imagesloaded@5/imagesloaded.pkgd.js"></script>
        <script src="https://unpkg.com/htmx.org@1.9.11/dist/htmx.js" integrity="sha384-l9bYT9SL4CAW0Hl7pAOpfRc18mys1b0wK4U8UtGnWOxPVbVMgrOdB+jyz/WY8Jue" crossorigin="anonymous"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.8/dist/cdn.min.js"></script>
    </head>
    <body>
        <div class="stream">
            <p>RSS Waterfall <a href="https://github.com/sekai-soft/rss-waterfall" target="_blank" style="font-size: 1em;">&lt;/&gt;</a></p>
        </div>
        <div class="grid stream" id="grid">
            <div class="grid-sizer"></div>
            IMAGES_HTML
        </div>
        <div class="tag-container stream">
            BUTTON_HTML
        </div>
        <script src="URL_FOR_SCRIPT_JS"></script>
    </body>
</html>
"""


def render_images_html(all_images: List[Image], max_images: int) -> str:
    images = all_images[:max_images]
    images_html = ''
    for image in images:
        images_html += GRID_ITEM_TEMPLATE \
            .replace('UID', image.uid) \
            .replace('IMAGE_URL', image.image_url) \
            .replace('URL', image.url)
    return images_html


def render_motto_button_html(max_uid: str) -> str:
    return MOTTO_BUTTON_TEMPLATE.replace('MAX_UID', max_uid)


def render_button_html(all_images: List[Image], max_images: int) -> str:
    if len(all_images) > max_images:
        max_uid = all_images[max_images - 1].uid
        return render_motto_button_html(max_uid)
    return OWARI_BUTTON


def render_index(all_images: List[Image], max_images: int, url_for_style_css: str, url_for_script_js: str) -> str:
    images_html = render_images_html(all_images, max_images)
    button_html = render_button_html(all_images, max_images)
    return INDEX_TEMPLATE \
        .replace('COUNT', str(len(all_images))) \
        .replace('IMAGES_HTML', images_html) \
        .replace('BUTTON_HTML', button_html) \
        .replace('URL_FOR_STYLE_CSS', url_for_style_css) \
        .replace('URL_FOR_SCRIPT_JS', url_for_script_js)
