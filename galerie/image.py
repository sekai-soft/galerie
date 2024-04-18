from typing import List
from dataclasses import dataclass
from bs4 import BeautifulSoup
from .item import Item
from .group import Group


@dataclass
class Image:
    image_url: str
    uid: str
    url: str
    groups: List[Group]


def uid_to_item_id(uid: str) -> str:
    return uid.rsplit('-', 1)[0]


def extract_images(html: str, item: Item) -> List[Image]:
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = soup.find_all('img')
    items = []
    for i, image_url in enumerate(image_urls):
        items.append(Image(
            image_url=image_url['src'],
            uid=f'{item.iid}-{i}',
            url=item.url,
            groups=item.groups))
    return items
