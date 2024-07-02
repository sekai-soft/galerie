from .group import Group
from typing import List
from dataclasses import dataclass


@dataclass
class Item:
    created_timestamp_seconds: int
    html: str
    iid: str
    url: str
    groups: List[Group]
    title: str
    feed_title: str
