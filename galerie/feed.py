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
    site_url: str
