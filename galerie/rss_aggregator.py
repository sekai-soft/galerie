from abc import abstractmethod, ABC
from typing import List, Optional, Dict
from dataclasses import dataclass
from .item import Item
from .group import Group
from .feed_filter import FeedFilter
from .feed import Feed


class AuthError(Exception): pass


@dataclass
class ConnectionInfo:
    aggregator_type: str
    host: str
    frontend_or_backend: bool


class RssAggregator(ABC):
    @abstractmethod
    def persisted_auth(self) -> str:
        pass

    @abstractmethod
    def get_groups(self) -> List[Group]:
        pass
    
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
    def add_feed(self, feed_url: str, gid: str) -> str:
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
