from abc import abstractmethod, ABC
from typing import List, Optional
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
    def get_group(self, group_id: str) -> Optional[Group]:
        pass

    @abstractmethod
    def get_unread_items_by_iid_ascending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:   
        pass

    @abstractmethod
    def get_unread_items_by_iid_descending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
        pass
    
    @abstractmethod
    def supports_get_unread_items_by_iid_descending() -> bool:
        pass

    @abstractmethod
    def get_unread_items_count(self, feed_filter: FeedFilter) -> int:
        pass
    
    @abstractmethod
    def mark_items_as_read_by_iid_ascending_and_feed_filter(self, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
        pass
    
    @abstractmethod
    def supports_mark_items_as_read_by_iid_ascending_and_feed_filter(self) -> bool:
        pass
    
    @abstractmethod
    def mark_items_as_read_by_group_id(self, group_id: Optional[str]):
        pass

    @abstractmethod
    def supports_mark_items_as_read_by_group_id(self) -> bool:
        pass

    @abstractmethod
    def connection_info(self) -> ConnectionInfo:
        pass

    @abstractmethod
    def supports_feed_management(self) -> bool:
        pass

    @abstractmethod
    def get_feeds(self) -> List[Feed]:
        pass

    @abstractmethod
    def convert_to_image_feed(self, fid: str):
        pass
    
    @abstractmethod
    def unconvert_from_image_feed(self, fid: str):
        pass
