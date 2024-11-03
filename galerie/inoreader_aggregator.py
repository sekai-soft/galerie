import json
from typing import List, Optional
from .item import Item, fix_nitter_url
from .group import Group
from .feed_filter import FeedFilter
from .rss_aggregator import RssAggregator, AuthError, ConnectionInfo
from inoreader.client import InoreaderClient


class InoreaderAggregator(RssAggregator):
    def __init__(self, app_id: str, app_key: str, access_token: str, refresh_token: str, expires_at: float):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.client = InoreaderClient(
            app_id=app_id,
            app_key=app_key,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at)
        self.client.check_token()

    def persisted_auth(self) -> str:
        try:
            self.client.userinfo()
        except Exception:
            raise AuthError()
        return json.dumps({
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at,
            'inoreader': True,
        })

    def get_groups(self) -> List[Group]:
        return []
    
    def get_group(self, group_id: str) -> Optional[Group]:
        return None

    def get_unread_items_by_iid_ascending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:   
        return []

    def get_unread_items_by_iid_descending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
        items = []
        articles = self.client.fetch_unread()
        for article in articles:
            items.append(Item(
                created_timestamp_seconds=article.published,  # TODO: maybe null
                html=article.content,
                iid=article.id,
                url=fix_nitter_url(article.link),
                groups=[],  # TODO
                title=article.title,
                feed_title=article.feed_title))
        return items
    
    def supports_get_unread_items_by_iid_descending(self) -> bool:
        return True

    def get_unread_items_count(self, feed_filter: FeedFilter) -> int:
        return 0
    
    def mark_items_as_read_by_iid_ascending_and_feed_filter(self, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
        pass
    
    def supports_mark_items_as_read_by_iid_ascending_and_feed_filter(self) -> bool:
        return False
    
    def mark_items_as_read_by_group_id(self, group_id: Optional[str]):
        pass

    def supports_mark_items_as_read_by_group_id(self) -> bool:
        return False

    def connection_info(self) -> ConnectionInfo:
        return ConnectionInfo(
            aggregator_type='Inoreader',
            host='www.inoreader.com',
            frontend_or_backend=True)
