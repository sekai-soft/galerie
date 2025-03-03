from typing import Optional
from dataclasses import dataclass


@dataclass
class FeedFilter:
    group_id: Optional[str]
