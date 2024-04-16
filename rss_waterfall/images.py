from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from .fever import get_unread_items


@dataclass
class Group:
    title: str
    gid: int


@dataclass
class Image:
    image_url: str
    uid: str
    url: str
    groups: List[Group]


def uid_to_item_id(uid: str) -> str:
    return uid.rsplit('-', 1)[0]


def extract_images(html: str, item: Dict) -> List[Image]:
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = soup.find_all('img')
    items = []
    for i, image_url in enumerate(image_urls):
        items.append(Image(
            image_url=image_url['src'],
            uid=f'{item['id']}-{i}',
            url=item['url'],
            groups=[Group(
                title=group['title'],
                gid=group['id']) for group in item['groups']]))
    return items


def get_images(fever_endpoint: str, fever_username: str, fever_password: str, after: Optional[int], group_id: Optional[str]) -> List[Image]:
    images = []
    for item in get_unread_items(fever_endpoint, fever_username, fever_password):
        should_include_for_after = not after or after < item['created_on_time']
        # the str(group['id']) is Fever API specific because Fever API's group IDs are int's but group_id is str
        should_include_for_group = not group_id or group_id in [str(group['id']) for group in item['groups']]
        if should_include_for_after and should_include_for_group:
            html = item['html']
            images += extract_images(html, item)
    return images
