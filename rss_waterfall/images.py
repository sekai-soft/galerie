from typing import List
from dataclasses import dataclass
from bs4 import BeautifulSoup
from .fever import get_unread_items


@dataclass
class Image:
    image_url: str
    uid: str


def extract_images(html: str, item_id: int) -> List[Image]:
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = soup.find_all('img')
    items = []
    for i, image_url in enumerate(image_urls):
        items.append(Image(image_url=image_url['src'], uid=f'{item_id}-{i}'))
    return items


def get_images(fever_endpoint: str, fever_username: str, fever_password: str) -> List[Image]:
    images = []
    for item in get_unread_items(fever_endpoint, fever_username, fever_password):
        html = item['html']
        images += extract_images(html, item['id'])
    return images
