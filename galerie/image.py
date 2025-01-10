from typing import List
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from .item import Item
from .group import Group
from .rss_aggregator import RssAggregator
from .miniflux_aggregator import MinifluxAggregator


MAX_IMAGES_PER_ITEM = 4


@dataclass
class Image:
    image_url: str
    uid: str
    url: str
    groups: List[Group]
    title: str
    feed_title: str
    more_images_count: int
    ui_extra: dict = field(default_factory=dict)


def uid_to_item_id(uid: str) -> str:
    return uid.rsplit('-', 1)[0]


def extract_images(items: List[Item]) -> List[Image]:
    images = []
    for item in items:
        soup = BeautifulSoup(item.html, 'html.parser')
        image_urls = soup.find_all('img')
        more_images_count = len(image_urls) - MAX_IMAGES_PER_ITEM
        if more_images_count < 0:
            more_images_count = 0
        image_urls = image_urls[:MAX_IMAGES_PER_ITEM]
        for i, image_url in enumerate(image_urls):
            images.append(Image(
                image_url=image_url['src'],
                uid=f'{item.iid}-{i}',
                url=item.url,
                title=item.title,
                feed_title=item.feed_title,
                groups=item.groups,
                more_images_count=more_images_count))
    return images


def convert_with_webp_cloud_endpoint(images: List[Image], aggregator: RssAggregator, webp_cloud_endpoint: str):
    if aggregator.connection_info().aggregator_type != 'Miniflux' or not webp_cloud_endpoint:
        return
    miniflux_aggregator = aggregator # type: MinifluxAggregator
    for image in images:
        image.image_url = image.image_url.replace(miniflux_aggregator.base_url + "/proxy", webp_cloud_endpoint + "/proxy")
