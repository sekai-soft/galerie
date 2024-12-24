from typing import Dict
from dataclasses import dataclass


@dataclass
class Feed:
    feed_url: str
    fid: str
    gid: str
    features: Dict
