from abc import abstractmethod, ABC
from typing import List, Optional, Dict
from dataclasses import dataclass
from .item import Item
from .group import Group, PREVIEW_GROUP_TITLE
from .feed_filter import FeedFilter
from .feed import Feed
from .feed_icon import FeedIcon


@dataclass
class ConnectionInfo:
    managed_or_self_hosted: bool
    host: Optional[str]


class RssAggregator(ABC):
    @abstractmethod
    def _get_groups(self) -> List[Group]:
        pass

    def get_groups(self) -> List[Group]:
        res = []
        for group in self._get_groups():
            if group.title != PREVIEW_GROUP_TITLE:
                res.append(group)
        return res

    @abstractmethod
    def get_unread_items_by_iid_ascending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:   
        pass

    @abstractmethod
    def get_unread_items_by_iid_descending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
        pass
    
    @abstractmethod
    def get_unread_items_count_by_group_ids(self, gids: List[str]) -> Dict[str, int]:
        pass
   
    @abstractmethod
    def mark_all_group_items_as_read(self, group_id: str):
        pass

    @abstractmethod
    def mark_all_items_as_read(self):
        pass

    @abstractmethod
    def connection_info(self) -> ConnectionInfo:
        pass

    @abstractmethod
    def get_feeds(self) -> List[Feed]:
        pass

    @abstractmethod
    def get_feed_items_by_iid_descending(self, fid: str) -> List[Item]:
        pass
    
    @abstractmethod
    def get_feed(self, fid: str) -> Feed:
        pass

    @abstractmethod
    def update_feed_group(self, fid: str, gid: str):
        pass

    @abstractmethod
    def add_feed(self, feed_url: str, gid: str, disabled: bool) -> Optional[str]:
        pass

    @abstractmethod
    def delete_feed(self, fid: str):
        pass

    @abstractmethod
    def mark_all_feed_items_as_read(self, fid: str):
        pass

    @abstractmethod
    def mark_last_unread(self, count: int):
        pass

    @abstractmethod
    def get_item(self, iid: str) -> Item:
        pass

    @abstractmethod
    def get_feed_icon(self, fid: str) -> FeedIcon:
        pass

    @abstractmethod
    def enable_feed(self, fid: str):
        pass

    @abstractmethod
    def create_group(self, title: str, hide_globally: bool) -> str:
        pass

    def get_preview_group(self) -> Optional[Group]:
        for group in self._get_groups():
            if group.title == PREVIEW_GROUP_TITLE:
                return group
        return None
    
    def get_feeds_by_group(self, gid: str) -> List[Feed]:
        res = []
        for feed in self.get_feeds():
            if feed.gid == gid:
                res.append(feed)
        return res

    def delete_feeds(self, gid: str):
        for feed in self.get_feeds():
            if feed.gid == gid:
                self.delete_feed(feed.fid)
