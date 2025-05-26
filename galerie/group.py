from dataclasses import dataclass


PREVIEW_GROUP_TITLE = '.preview'


@dataclass
class Group:
    title: str
    gid: str
    feed_count: int
