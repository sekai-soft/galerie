from abc import abstractmethod, ABC
from typing import List, Tuple, Optional
from .item import Item
from .group import Group
from .feed_filter import FeedFilter


class AuthError(Exception): pass


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
    def get_unread_items_count(self, feed_filter: FeedFilter) -> int:
        pass
    
    @abstractmethod
    def mark_items_as_read(self, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
        pass
