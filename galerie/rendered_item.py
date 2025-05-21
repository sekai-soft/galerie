from typing import List, Optional
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from .item import Item
from .group import Group


MAX_RENDERED_ITEMS_COUNT = 4


@dataclass
class RenderedItem:
    uid: str
    url: str
    groups: List[Group]
    title: str
    feed_title: str
    fid: str
    iid: str

    image_url: str = ''
    video_url: str = ''
    text: str = ''
    left_rendered_items: int = 0
    ui_extra: dict = field(default_factory=dict)


def convert_rendered_item(item: Item, ignore_rendered_items_cap: Optional[bool]=False) -> RenderedItem:
    res = []

    soup = BeautifulSoup(item.html, 'html.parser')
    target_elements = soup.find_all(['img', 'video'])
    total_target_elements = len(target_elements)
    if not ignore_rendered_items_cap:
        target_elements = target_elements[:MAX_RENDERED_ITEMS_COUNT]

    for i, target_element in enumerate(target_elements):
        if target_element.name == 'img':
            image_url = target_element.get('src', '')
            video_url = ''

        elif target_element.name == 'video':
            image_url = target_element.get('poster', '')
            source_element = target_element.find('source')
            video_url = source_element.get('src', '') if source_element else target_element.get('src', '')

        res.append(RenderedItem(
            uid=f'{item.iid}-{i}',
            url=item.url,
            groups=item.groups,
            title=item.title if item.title else "(No title)",
            feed_title=item.feed_title,
            fid=item.fid,
            iid=item.iid,

            image_url=image_url,
            video_url=video_url,
            text=item.text,
            left_rendered_items=total_target_elements - MAX_RENDERED_ITEMS_COUNT,))

    return res


def convert_rendered_items(items: List[Item]) -> List[RenderedItem]:
    res = []
    for item in items:
        res.extend(convert_rendered_item(item))
    return res
