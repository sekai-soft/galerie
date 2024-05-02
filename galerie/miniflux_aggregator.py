import os
import requests
import hashlib
import json
import miniflux
from datetime import datetime
from typing import List, Tuple, Optional
from .item import Item
from .group import Group
from .feed_filter import FeedFilter
from .rss_aggregator import RssAggregator, AuthError


def _category_dict_to_group(category_dict: dict) -> Group:
    return Group(
        gid=str(category_dict['id']),
        title=category_dict['title'],
    )


def _entry_dict_to_item(entry_dict: dict) -> Item:
    return Item(
        created_timestamp_seconds=int(datetime.strptime(
            entry_dict['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()),
        html=entry_dict['content'],
        iid=str(entry_dict['id']),
        url=entry_dict['url'],
        groups=[_category_dict_to_group(entry_dict['feed']['category'])],
    )


class MinifluxAggregator(RssAggregator):
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.client = miniflux.Client(base_url, username, password)
    
    def persisted_auth(self) -> str:
        try:
            self.client.me()
        except miniflux.ClientError:
            raise AuthError()
        return json.dumps({
            'base_url': self.base_url,
            'username': self.username,
            'password': self.password
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
    
    def get_unread_items_by_iid_descending(self, count: int, to_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
        raise NotImplementedError()

    def supports_get_unread_items_by_iid_descending(self) -> bool:
        return True
    
    def get_unread_items_count(self, feed_filter: FeedFilter) -> int:
        entries = self.client.get_entries(
            status='unread',
            order='id',
            direction='asc',
            published_after=feed_filter.created_after_seconds,
            category_id=None if feed_filter.group_id is None else int(feed_filter.group_id)
        )
        return entries['total']
    
    def mark_items_as_read(self, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
        pass
