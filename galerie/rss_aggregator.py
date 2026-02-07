from abc import abstractmethod, ABC
from typing import List, Optional, Dict
from dataclasses import dataclass
from .item import Item
from .group import Group
from .feed import Feed
from .feed_icon import FeedIcon
from .twitter import extract_twitter_handle_from_url, extract_twitter_handle_from_url


@dataclass
class ConnectionInfo:
    managed_or_self_hosted: bool
    host: Optional[str]


class RssAggregator(ABC):  
    @abstractmethod
    def get_groups(self) -> List[Group]:
        pass

    @abstractmethod
    def get_items(self, count: int, from_iid_exclusive: Optional[str], group_id: Optional[str], sort_by_id_descending: bool, include_read: bool) -> List[Item]:
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
    def mark_items_as_read(self, iids: List[str]):
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
    def add_feed(self, feed_url: str, gid: str) -> Optional[str]:
        pass

    @abstractmethod
    def delete_feed(self, fid: str):
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
    def create_group(self, title: str) -> str:
        pass

    @abstractmethod
    def get_feeds_by_group_id(self, gid: str) -> List[Feed]:
        pass

    @abstractmethod
    def rename_group(self, gid: str, new_title: str):
        pass

    @abstractmethod
    def delete_group(self, gid: str):
        pass

    @abstractmethod
    def get_username(self) -> str:
        pass

    def delete_feeds_by_group_id(self, gid: str):
        for feed in self.get_feeds_by_group_id(gid):
            self.delete_feed(feed.fid)

    def get_group(self, gid: str) -> Optional[Group]:
        for group in self.get_groups():
            if group.gid == gid:
                return group
        return None

    def find_feed_by_url(self, finding_url: str) -> Optional[Feed]:
        finding_twitter_handle = extract_twitter_handle_from_url(finding_url)

        for feed in self.get_feeds():
            feed_url = feed.url
            feed_twitter_handle = extract_twitter_handle_from_url(feed_url)
            if (feed_url == finding_url) or (finding_twitter_handle and finding_twitter_handle == feed_twitter_handle):
                return feed

        return None
