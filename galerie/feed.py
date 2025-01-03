from typing import Dict
from dataclasses import dataclass


@dataclass
class Feed:
    fid: str
    gid: str
    features: Dict
