import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
from rss_waterfall.fever import get_unread_items
from rss_waterfall.rss import extract_images


def get_env_or_bust(key: str) -> str:
    if key not in os.environ:
        raise ValueError(f"Missing required environment variable: {key}")
    return os.environ[key]

load_dotenv()
fever_endpoint = get_env_or_bust('FEVER_ENDPOINT')
fever_username = get_env_or_bust('FEVER_USERNAME')
fever_password = get_env_or_bust('FEVER_PASSWORD')
max_images = int(os.getenv('MAX_IMAGES', '15'))

app = Flask(__name__, static_url_path='/static')


def get_images():
    images = []
    for item in get_unread_items(fever_endpoint, fever_username, fever_password):
        html = item['html']
        images += extract_images(html, item['id'])
    return images


@app.route("/")
def index():
    images = get_images()
    return render_template(
        'index.jinja',
        count=len(images),
        images=images[: max_images])


GRID_ITEM_TEMPLATE = """<div class="grid-item" id="UID">
    <img class="item-image" src="IMAGE_URL" />
</div>"""


MOTTO_BUTTON_TEMPLATE = """<div
    id="motto"
    class="tag"
    hx-swap-oob="true"
    hx-get="/more?max_uid=MAX_UID"
    hx-target="#grid"
    hx-swap="beforeend"
>もっと</div>"""


OWARI_BUTTON = """<div
    id="motto"
    class="tag"
    hx-swap-oob="true"
>終わり</div>"""


@app.route('/more')
def more():
    max_uid = request.args.get('max_uid')
    all_images = get_images()
    max_uid_index = -1
    for i, image in enumerate(all_images):
        if image.uid == max_uid:
            max_uid_index = i
            break
    more_images = all_images[max_uid_index + 1: max_uid_index + 1 + max_images]

    if not more_images:
        return OWARI_BUTTON
    
    more_html = map(
        lambda image: GRID_ITEM_TEMPLATE.replace('UID', image.uid).replace('IMAGE_URL', image.image_url),
        more_images)
    more_html = ''.join(more_html)

    motto_button = MOTTO_BUTTON_TEMPLATE.replace('MAX_UID', more_images[-1].uid)

    return more_html + motto_button
