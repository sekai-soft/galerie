from dataclasses import dataclass


@dataclass
class Group:
    title: str
    gid: str
    feed_count: int
