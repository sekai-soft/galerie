import miniflux
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from .item import Item
from .group import Group
from .rss_aggregator import RssAggregator, ConnectionInfo
from .feed import Feed
from .twitter import fix_nitter_url, fix_nitter_rt_title, fix_nitter_urls_in_text, fix_nitter_rt_in_text, is_nitter_url, fix_nitter_feed_title
from .feed_icon import FeedIcon


TIMEOUT = 5


def _category_dict_to_group(category_dict: dict) -> Group:
    return Group(
        gid=str(category_dict['id']),
        title=category_dict['title'],
        feed_count=category_dict.get('feed_count', 0),
    )


def parse_published_at(date_string: str) -> datetime:
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"time data '{date_string}' doesn't match known formats")


def entry_dict_to_item(entry_dict: dict) -> Item:
    url = entry_dict['url']

    html = entry_dict['content']
    if entry_dict['enclosures']:
        for enclosure in entry_dict['enclosures']:
            if enclosure['mime_type'].startswith('image/'):
                html += f'<img src="{enclosure["url"]}">'

    text = BeautifulSoup(html, 'html.parser').get_text(" ", strip=True)
    title = entry_dict['title']
    feed_title = entry_dict['feed']['title']

    if is_nitter_url(url):
        url = fix_nitter_url(url)
        text = fix_nitter_urls_in_text(text)
        text = fix_nitter_rt_in_text(text)
        title = fix_nitter_rt_title(title)
        feed_title = fix_nitter_feed_title(feed_title)

    return Item(
        published_at=parse_published_at(entry_dict['created_at']),
        html=html,
        iid=str(entry_dict['id']),
        url=url,
        group=_category_dict_to_group(entry_dict['feed']['category']),
        title=title,
        feed_title=feed_title,
        fid=str(entry_dict['feed_id']),
        text=text,
        unread_or_not=entry_dict['status'] == 'unread',
    )


def _feed_dict_to_feed(feed_dict: dict) -> Feed:
    feed_url = feed_dict['feed_url']

    title = feed_dict['title']
    if is_nitter_url(feed_url):
        title = fix_nitter_feed_title(title)

    return Feed(
        fid=str(feed_dict['id']),
        gid=str(feed_dict['category']['id']),
        url=feed_dict['feed_url'],
        title=title,
        group_title=feed_dict['category']['title'],
        error=feed_dict.get('parsing_error_count', 0) > 0,
        site_url=fix_nitter_url(feed_dict.get('site_url', ''))
    )


class MinifluxAggregator(RssAggregator):
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        managed_or_self_hosted: bool):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.client = miniflux.Client(base_url, username, password, timeout=TIMEOUT)
        self.managed_or_self_hosted = managed_or_self_hosted

    def get_groups(self) -> List[Group]:
        _endpoint = self.client._get_endpoint("/categories?counts=true")
        _response = self.client._session.get(_endpoint, timeout=self.client._timeout)
        if _response.status_code != 200:
            self.client._handle_error_response(_response)
        res = _response.json()
        return list(map(_category_dict_to_group, res))

    def get_items(self, count: int, from_iid_exclusive: Optional[str], group_id: Optional[str], sort_by_id_descending: bool, include_read: bool, after: Optional[int] = None, before: Optional[int] = None) -> List[Item]:
        kwargs = {
            "status": ['unread', 'read'] if include_read else 'unread',
            "order": 'id',
            "direction": 'desc' if sort_by_id_descending else 'asc',
            "limit": count,
            "category_id": None if group_id is None else int(group_id)
        }

        if after is not None:
            kwargs["after"] = after

        if before is not None:
            kwargs["before"] = before

        before_or_after_entry_id = None if from_iid_exclusive is None else int(from_iid_exclusive)
        if sort_by_id_descending:
            kwargs["before_entry_id"] = before_or_after_entry_id
        else:
            kwargs["after_entry_id"] = before_or_after_entry_id

        entries = self.client.get_entries(**kwargs)

        return list(map(entry_dict_to_item, entries['entries']))
   
    def get_unread_items_count_by_group_ids(self, gids: List[str], include_read: bool) -> Dict[str, int]:
        res = {}
        for gid in gids:
            res[gid] = 0

        feeds = self.get_feeds()
        unread_feed_counters = self.client.get_feed_counters()["unreads"]
        read_feed_counters = self.client.get_feed_counters()["reads"]

        for feed in feeds:
            feed_id = feed.fid
            gid = feed.gid
            if feed_id in unread_feed_counters:
                res[gid] += unread_feed_counters[feed_id]
            if include_read and feed_id in read_feed_counters:
                res[gid] += read_feed_counters[feed_id]

        return res
    
    def mark_all_group_items_as_read(self, group_id: str):
        self.client.mark_category_entries_as_read(category_id=int(group_id))

    def mark_all_items_as_read(self):
        self.client.mark_user_entries_as_read(self.client.me()['id'])

    def connection_info(self) -> ConnectionInfo:
        return ConnectionInfo(
            managed_or_self_hosted=self.managed_or_self_hosted,
            host=urlparse(self.base_url).hostname,
        )

    def get_feeds(self) -> List[Feed]:
        return list(map(_feed_dict_to_feed, self.client.get_feeds()))

    def get_feed_items_by_iid_descending(self, fid: str) -> List[Item]:
        entries = self.client.get_feed_entries(
            int(fid),
            order='id',
            direction='desc'
        )
        return list(map(entry_dict_to_item, entries['entries']))

    def get_feed(self, fid: str) -> Feed:
        return _feed_dict_to_feed(self.client.get_feed(int(fid)))

    def update_feed_group(self, fid: str, gid: str):
        self.client.update_feed(int(fid), category_id=int(gid))

    def add_feed(self, feed_url: str, gid: str) -> Optional[str]:
        try:
            fid = self.client.create_feed(
                feed_url,
                category_id=int(gid),
            )
        except miniflux.ClientError as e:
            if e.get_error_reason() == "parser: unable to detect feed format":
                return None
            raise e
        return str(fid)

    def delete_feed(self, fid: str):
        self.client.delete_feed(int(fid))

    def mark_all_feed_items_as_read(self, fid: str):
        self.client.mark_feed_entries_as_read(int(fid))

    def mark_last_unread(self, count: int):
        entries = self.client.get_entries(
            order='id',
            direction='desc',
            limit=count
        )
        entry_ids = [entry['id'] for entry in entries['entries']]
        self.client.update_entries(entry_ids, 'unread')

    def get_item(self, iid: str) -> Item:
        return entry_dict_to_item(self.client.get_entry(int(iid)))

    def get_item_and_entry_dict(self, iid: str) -> tuple[Item, dict]:
        entry_dict = self.client.get_entry(int(iid))
        item = entry_dict_to_item(entry_dict)
        return item, entry_dict

    def get_feed_icon(self, fid: str) -> Optional[FeedIcon]:
        try:
            fi = self.client.get_feed_icon(int(fid))
            return FeedIcon(
                data=fi['data'],
                mime_type=fi['mime_type']
            )
        except Exception:
            return None

    def create_group(self, title: str) -> str:
        return str(self.client.create_category(title)["id"])

    def get_feeds_by_group_id(self, gid: str) -> List[Feed]:
        feeds = self.client.get_category_feeds(int(gid))
        return list(map(_feed_dict_to_feed, feeds))

    def rename_group(self, gid: str, new_title: str):
        self.client.update_category(int(gid), new_title)

    def delete_group(self, gid: str):
        self.client.delete_category(int(gid))

    def get_username(self) -> str:
        return self.client.me()['username']
