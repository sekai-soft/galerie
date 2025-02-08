import re
from .group import Group
from typing import List
from dataclasses import dataclass


def fix_nitter_url(url: str) -> str:
    pattern = re.compile(r'nitter-[^.]+\.fly\.dev')
    if pattern.search(url):
        return pattern.sub('twitter.com', url)
    return url


@dataclass
class Item:
    created_timestamp_seconds: int
    html: str
    iid: str
    url: str
    groups: List[Group]
    title: str
    feed_title: str
    fid: str
