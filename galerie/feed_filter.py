from typing import Optional
from dataclasses import dataclass


@dataclass
class FeedFilter:
    created_after_seconds: Optional[int]
    group_id: Optional[str]
