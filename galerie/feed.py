from typing import Dict
from dataclasses import dataclass


@dataclass
class Feed:
    fid: str
    gid: str
    url: Dict
    title: str
    group_title: str
    error: bool
    error_reason: str
    site_url: str
    order_added: int
