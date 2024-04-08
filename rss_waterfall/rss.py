from typing import List
from dataclasses import dataclass
from bs4 import BeautifulSoup


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
