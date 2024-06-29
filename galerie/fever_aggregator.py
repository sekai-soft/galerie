import os
import requests
import hashlib
import json
from urllib.parse import urlparse
from typing import List, Tuple, Optional
from .item import Item
from .group import Group
from .feed_filter import FeedFilter
from .rss_aggregator import RssAggregator, AuthError, ConnectionInfo


def _compute_api_key(username: str, password: str):
    username_plus_password = username + ':' + password
    return hashlib.md5(username_plus_password.encode()).hexdigest()


def _group_dict_to_group(group_dict: dict) -> Group:
    return Group(
        title=group_dict['title'],
        # the str casting here is Fever API specific because Fever API's IDs are int's but str is required
        gid=str(group_dict['id'])
    )


def _item_dict_to_item(item_dict: dict, group_dicts: List[dict]) -> Item:
    return Item(
        created_timestamp_seconds=item_dict['created_on_time'],
        html=item_dict['html'],
        # the str casting here is Fever API specific because Fever API's IDs are int's but str is required
        iid=str(item_dict['id']),
        url=item_dict['url'],
        groups=list(map(_group_dict_to_group, group_dicts)),
    )


class FeverAggregator(RssAggregator):
    def __init__(
        self,
        endpoint: str,
        username: str,
        password: str,
        frontend_or_backend: bool):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.api_key = _compute_api_key(username, password)
        self.frontend_or_backend = frontend_or_backend

    def persisted_auth(self) -> str:
        self._verify_auth()
        return json.dumps({
            'endpoint': self.endpoint,
            'username': self.username,
            'password': self.password
        })

    def _call_fever(self, path: str):
        if os.getenv('DEBUG', '0') == '1':
            print(f'Calling fever {path}')
        res = requests.post(self.endpoint + path, data={'api_key': self.api_key})
        res.raise_for_status()
        return res.json()
    
    def _verify_auth(self):
        auth_res = self._call_fever('/?api')
        if 'auth' not in auth_res or auth_res['auth'] != 1:
            raise AuthError()

    def _get_groups(self) -> Tuple[List[dict], List[dict]]:
        groups_res = self._call_fever('/?api&groups')
        return groups_res['groups'], groups_res['feeds_groups']

    def get_groups(self) -> List[Group]:
        groups, _ = self._get_groups()
        return list(map(_group_dict_to_group, groups))

    def get_group(self, group_id: str) -> Optional[Group]:
        groups = self.get_groups()
        for group in groups:
            if group.gid == group_id:
                return group
        return None

    def get_unread_items_by_iid_ascending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:   
        groups, feeds_groups = self._get_groups()
        group_by_id = {group['id']: group for group in groups}
        groups_by_feed_id = {}
        for feeds_group in feeds_groups:
            group_id = feeds_group['group_id']
            for feed_id in feeds_group['feed_ids'].split(','):
                if feed_id not in groups_by_feed_id:
                    groups_by_feed_id[feed_id] = []
                groups_by_feed_id[feed_id].append(group_by_id[group_id])

        unread_item_ids_res = self._call_fever('/?api&unread_item_ids')
        unread_item_ids = unread_item_ids_res['unread_item_ids']
        if unread_item_ids == '':
            return []
        unread_item_ids = list(sorted(map(int, unread_item_ids.split(','))))

        if not from_iid_exclusive:
            # start from beginning
            unread_item_id_index = 0
        else:
            unread_item_id_index = unread_item_ids.index(int(from_iid_exclusive)) + 1

        unread_items = []  # type: List[Item]
        while unread_item_id_index < len(unread_item_ids) and len(unread_items) < count:
            # the &items&since_id query later looks like it's exclusive, e.g. the unread_item_ids[unread_item_id_index] item will not be included
            # hence need to -1 to make sure the unread_item_ids[unread_item_id_index] item is also included
            since_id = unread_item_ids[unread_item_id_index] - 1
            items_res = self._call_fever(f'/?api&items&since_id={since_id}')
            items = items_res['items']
            if not items:
                break
            batch_items = []
            for item in items:
                item_groups = groups_by_feed_id.get(str(item['feed_id']), [])
                batch_items.append(_item_dict_to_item(item, item_groups))
            batch_unread_items = []
            for item in batch_items:
                is_unread = int(item.iid) in unread_item_ids
                is_after = not feed_filter.created_after_seconds or feed_filter.created_after_seconds < item.created_timestamp_seconds
                is_group = not feed_filter.group_id or feed_filter.group_id in [group.gid for group in item.groups]
                if is_unread:
                    # we are guaranteed to have at least one unread item
                    # because since_id was guaranteed to exclusively start from an unread item
                    # hence unread_item_id_index will always advance
                    unread_item_id_index += 1
                    if is_after and is_group:
                        batch_unread_items.append(item)
            batch_unread_items = batch_unread_items[:count - len(unread_items)]
            unread_items += batch_unread_items

        return unread_items

    def get_unread_items_by_iid_descending(self, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
        raise NotImplementedError()

    def supports_get_unread_items_by_iid_descending(self) -> bool:
        return False

    def get_unread_items_count(self, _: FeedFilter) -> int:
        unread_item_ids_res = self._call_fever('/?api&unread_item_ids')
        unread_item_ids = unread_item_ids_res['unread_item_ids']
        if unread_item_ids == '':
            return 0
        return len(unread_item_ids.split(','))
    
    def mark_items_as_read_by_iid_ascending_and_feed_filter(self, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
        groups, feeds_groups = self._get_groups()
        group_by_id = {group['id']: group for group in groups}
        groups_by_feed_id = {}
        for feeds_group in feeds_groups:
            group_id = feeds_group['group_id']
            for feed_id in feeds_group['feed_ids'].split(','):
                if feed_id not in groups_by_feed_id:
                    groups_by_feed_id[feed_id] = []
                groups_by_feed_id[feed_id].append(group_by_id[group_id])

        unread_item_ids_res = self._call_fever('/?api&unread_item_ids')
        unread_item_ids = unread_item_ids_res['unread_item_ids']
        if unread_item_ids == '':
            return []
        unread_item_ids = list(sorted(map(int, unread_item_ids.split(','))))

        if not to_iid_inclusive:
            # end at end
            end_at_iid_index_exclusive = len(unread_item_ids)
        else:
            end_at_iid_index_exclusive = unread_item_ids.index(int(to_iid_inclusive)) + 1

        marked_as_read_count = 0
        unread_item_id_index = 0
        while unread_item_id_index < end_at_iid_index_exclusive:
            # the &items&since_id query later looks like it's exclusive, e.g. the unread_item_ids[unread_item_id_index] item will not be included
            # hence need to -1 to make sure the unread_item_ids[unread_item_id_index] item is also included
            since_id = unread_item_ids[unread_item_id_index] - 1
            items_res = self._call_fever(f'/?api&items&since_id={since_id}')
            items = items_res['items']
            if not items:
                break
            batch_items = []
            for item in items:
                item_groups = groups_by_feed_id.get(str(item['feed_id']), [])
                batch_items.append(_item_dict_to_item(item, item_groups))
            for item in batch_items:
                is_unread = int(item.iid) in unread_item_ids
                is_after = not feed_filter.created_after_seconds or feed_filter.created_after_seconds < item.created_timestamp_seconds
                is_group = not feed_filter.group_id or feed_filter.group_id in [group.gid for group in item.groups]
                if is_unread:
                    # we are guaranteed to have at least one unread item
                    # because since_id was guaranteed to exclusively start from an unread item
                    # hence unread_item_id_index will always advance
                    unread_item_id_index += 1
                    if is_after and is_group:
                        self._call_fever(f'/?api&mark=item&as=read&id={item.iid}')
                        marked_as_read_count += 1
        
        return marked_as_read_count

    def supports_mark_items_as_read_by_iid_ascending_and_feed_filter(self) -> bool:
        return True

    def mark_items_as_read_by_group_id(self, group_id: Optional[str]):
        pass

    def supports_mark_items_as_read_by_group_id(self) -> bool:
        return False

    def connection_info(self) -> ConnectionInfo:
        return ConnectionInfo(
            aggregator_type='Fever',
            host=urlparse(self.endpoint).hostname,
            frontend_or_backend=self.frontend_or_backend
        )
