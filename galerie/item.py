import datetime
from .group import Group
from typing import List
from dataclasses import dataclass


@dataclass
class Item:
    published_at: datetime.datetime
    html: str
    iid: str
    url: str
    group: Group
    title: str
    feed_title: str
    fid: str
    text: str
    unread_or_not: bool
