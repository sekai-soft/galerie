import json
import miniflux
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional
from urllib.parse import quote
from .item import Item, fix_nitter_url
from .group import Group
from .feed_filter import FeedFilter
from .rss_aggregator import RssAggregator, AuthError, ConnectionInfo
from .feed import Feed
from .parse_feed_features import parse_feed_features


def _category_dict_to_group(category_dict: dict) -> Group:
    return Group(
        gid=str(category_dict['id']),
        title=category_dict['title'],
    )


def _entry_dict_to_item(entry_dict: dict) -> Item:
    html = entry_dict['content']
    if entry_dict['enclosures']:
        for enclosure in entry_dict['enclosures']:
            if enclosure['mime_type'].startswith('image/'):
                html += f'<img src="{enclosure["url"]}">'
    return Item(
        created_timestamp_seconds=int(datetime.strptime(
            entry_dict['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
        html=html,
        iid=str(entry_dict['id']),
        url=fix_nitter_url(entry_dict['url']),
        groups=[_category_dict_to_group(entry_dict['feed']['category'])],
        title=entry_dict['title'],
        feed_title=entry_dict['feed']['title']
    )


class MinifluxAggregator(RssAggregator):
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        frontend_or_backend: bool):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.client = miniflux.Client(base_url, username, password)
        self.frontend_or_backend = frontend_or_backend
    
    def persisted_auth(self) -> str:
        try:
            self.client.me()
        except miniflux.ClientError:
            raise AuthError()
        return json.dumps({
            'base_url': self.base_url,
            'username': self.username,
            'password': self.password,
            'miniflux': True,
        })

    def get_groups(self) -> List[Group]:
        return list(map(_category_dict_to_group, self.client.get_categories()))

    def get_group(self, group_id: str) -> Optional[Group]:
        for group in self.get_groups():
            if group.gid == group_id:
                return group
        return None 

    def get_unread_items_by_iid_ascending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
        entries = self.client.get_entries(
            status='unread',
            order='id',
            direction='asc',
            limit=count,
            after_entry_id=None if from_iid_exclusive is None else int(from_iid_exclusive),
            published_after=feed_filter.created_after_seconds,
            category_id=None if feed_filter.group_id is None else int(feed_filter.group_id)
        )
        return list(map(_entry_dict_to_item, entries['entries']))
    
    def get_unread_items_by_iid_descending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
        entries = self.client.get_entries(
            status='unread',
            order='id',
            direction='desc',
            limit=count,
            before_entry_id=None if from_iid_exclusive is None else int(from_iid_exclusive),
            published_after=feed_filter.created_after_seconds,
            category_id=None if feed_filter.group_id is None else int(feed_filter.group_id)
        )
        return list(map(_entry_dict_to_item, entries['entries']))

    def supports_get_unread_items_by_iid_descending(self) -> bool:
        return True
    
    def get_unread_items_count(self, feed_filter: FeedFilter) -> int:
        entries = self.client.get_entries(
            status='unread',
            order='id',
            direction='asc',
            published_after=feed_filter.created_after_seconds,
            category_id=None if feed_filter.group_id is None else int(feed_filter.group_id),
            limit=1
        )
        return entries['total']
    
    def mark_items_as_read_by_iid_ascending_and_feed_filter(self, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
        pass

    def supports_mark_items_as_read_by_iid_ascending_and_feed_filter(self) -> bool:
        return False

    def mark_items_as_read_by_group_id(self, group_id: Optional[str]):
        if group_id is not None:
            self.client.mark_category_entries_as_read(category_id=int(group_id))
        else:
            self.client.mark_user_entries_as_read(self.client.me()['id'])

    def supports_mark_items_as_read_by_group_id(self) -> bool:
        return True

    def connection_info(self) -> ConnectionInfo:
        return ConnectionInfo(
            aggregator_type='Miniflux',
            host=urlparse(self.base_url).hostname,
            frontend_or_backend=self.frontend_or_backend
        )
    
    def supports_feed_management(self) -> bool:
        return True

    def get_feeds(self) -> List[Feed]:
        feeds = []
        for f in self.client.get_feeds():
            feeds.append(Feed(
                feed_url=f['feed_url'],
                fid=str(f['id']),
                gid=str(f['category']['id']),
                features=parse_feed_features(f['feed_url'])
            ))
        return feeds

    def update_feed_to_image_feed(self, fid: str):
        feed_url = self.client.get_feed(int(fid))['feed_url']
        self.client.update_feed(int(fid), feed_url=f'https://rss-lambda.xyz/to_image_feed?url={quote(feed_url)}')
