from abc import abstractmethod, ABC
from typing import List, Tuple, Optional
from .item import Item
from .group import Group
from .feed_filter import FeedFilter


class AuthError(Exception): pass


class RssAggregator(ABC):
    @abstractmethod
    def persisted_auth() -> str:
        pass

    @abstractmethod
    def get_groups() -> List[Group]:
        pass
    
    @abstractmethod
    def get_group(group_id: str) -> Optional[Group]:
        pass

    @abstractmethod
    def get_unread_items_by_iid_ascending(count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:   
        pass

    @abstractmethod
    def get_unread_items_count(feed_filter: FeedFilter) -> int:
        pass
    
    @abstractmethod
    def mark_items_as_read(endpoint: str, username: str, password: str, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
        pass
