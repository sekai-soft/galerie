import os
import base64
import datetime
from typing import List, Optional
from urllib.parse import unquote, urlparse
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from .item import Item
from .group import Group
from .twitter import get_nitter_base_url, fix_shareable_twitter_url, TWITTER_VIDEO_CDN_HOST, TWITTER_MEDIA_CDN_URL


@dataclass
class RenderedItem:
    uid: str
    url: str
    group: Group
    title: str
    feed_title: str
    fid: str
    iid: str
    unread_or_not: bool
    published_at: datetime.datetime

    image_url: str = ''
    video_url: str = ''
    video_thumbnail_url: str = ''
    text: str = ''
    video_count: int = 0
    image_count: int = 0

    shareable_url: str = field(init=False)

    def __post_init__(self):
        self.shareable_url = fix_shareable_twitter_url(self.url)
        self.shareable_url = unquote(self.shareable_url)


def get_media_proxy_custom_url() -> str:
    url = os.environ.get('MEDIA_PROXY_CUSTOM_URL', '')
    if not url.endswith('/'):
        url += '/'
    return url


def fix_proxied_media_url(url: str) -> str:
    media_proxy_custom_url = get_media_proxy_custom_url()

    if url.startswith(media_proxy_custom_url):
        encoded_url = url[len(media_proxy_custom_url):]
        decoded_url = base64.urlsafe_b64decode(encoded_url).decode('utf-8')

        if decoded_url.startswith(get_nitter_base_url()):
            twitter_media_path = unquote(urlparse(decoded_url).path.split('/')[-1])
            if twitter_media_path.startswith(TWITTER_VIDEO_CDN_HOST):
                return 'https://' + twitter_media_path
            return TWITTER_MEDIA_CDN_URL + twitter_media_path

        return decoded_url

    return url


def convert_rendered_item(item: Item, max_rendered_items: int, ignore_rendered_items_cap: Optional[bool]=False) -> List[RenderedItem]:
    soup = BeautifulSoup(item.html, 'html.parser')
    
    target_elements = []
    image_count, video_count = 0, 0
    for target_element in soup.find_all(['img', 'video']):
        if target_element.name == 'img':
            image_count += 1
        elif target_element.name == 'video':
            source_element = target_element.find('source')
            if not source_element or not source_element.get('src'):
                continue
            video_count += 1
        target_elements.append(target_element)

    if not ignore_rendered_items_cap:
        target_elements = target_elements[:max_rendered_items]

    res = []
    for i, target_element in enumerate(target_elements):
        if target_element.name == 'img':
            image_url = target_element.get('src', '')
            video_url = ''
            video_thumbnail_url = ''

        elif target_element.name == 'video':
            image_url = ''
            source_element = target_element.find('source')
            video_url = source_element.get('src', '') if source_element else target_element.get('src', '')
            video_thumbnail_url = target_element.get('poster', '')

        res.append(RenderedItem(
            uid=f'{item.iid}-{i}',
            url=item.url,
            group=item.group,
            title=item.title if item.title else "(No title)",
            feed_title=item.feed_title,
            fid=item.fid,
            iid=item.iid,
            unread_or_not=item.unread_or_not,
            published_at=item.published_at,

            image_url=fix_proxied_media_url(image_url),
            video_url=fix_proxied_media_url(video_url),
            video_thumbnail_url=fix_proxied_media_url(video_thumbnail_url),
            text=item.text if item.text else "(No text)",
            video_count=video_count,
            image_count=image_count,))

    return res


def convert_rendered_items(items: List[Item], max_rendered_items: int) -> tuple[List[RenderedItem], List[str]]:
    rendered_items = []
    iids_without_media = []
    for item in items:
        converted = convert_rendered_item(item, max_rendered_items)
        if converted:
            rendered_items.extend(converted)
        elif item.unread_or_not:
            iids_without_media.append(item.iid)
    return rendered_items, iids_without_media
