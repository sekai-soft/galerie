from typing import List
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from .item import Item
from .group import Group


@dataclass
class Image:
    image_url: str
    uid: str
    url: str
    groups: List[Group]
    title: str
    feed_title: str
    ui_extra: dict = field(default_factory=dict)


def uid_to_item_id(uid: str) -> str:
    return uid.rsplit('-', 1)[0]


def extract_images(items: List[Item]) -> List[Image]:
    images = []
    for item in items:
        soup = BeautifulSoup(item.html, 'html.parser')
        image_urls = soup.find_all('img')
        for i, image_url in enumerate(image_urls):
            images.append(Image(
                image_url=image_url['src'],
                uid=f'{item.iid}-{i}',
                url=item.url,
                title=item.title,
                feed_title=item.feed_title,
                groups=item.groups))
    return images
