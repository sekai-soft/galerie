import requests
import hashlib
from typing import List, Tuple, Optional
from .item import Item
from .group import Group
from .image import uid_to_item_id
from .feed_filter import FeedFilter


class FeverAuthError(Exception):
    pass


def fever_auth(endpoint: str, username: str, password: str) -> str:
    api_key = fever_get_api_key(username, password)

    auth_res = requests.post(endpoint + '/?api', data={'api_key': api_key})
    auth_res.raise_for_status()
    auth_res = auth_res.json()
    if 'auth' not in auth_res or auth_res['auth'] != 1:
        raise FeverAuthError()
    return api_key


def fever_get_api_key(username: str, password: str):
    username_plus_password = username + ':' + password
    return hashlib.md5(username_plus_password.encode()).hexdigest()

def _get_groups(endpoint: str, username: str, password: str) -> Tuple[List[dict], List[dict]]:
    api_key = fever_get_api_key(username, password)
    groups_res = requests.post(endpoint + '/?api&groups', data={'api_key': api_key})
    groups_res.raise_for_status()
    return groups_res.json()['groups'], groups_res.json()['feeds_groups']


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


def get_groups(endpoint: str, username: str, password: str):
    groups, _ = _get_groups(endpoint, username, password)
    return list(map(_group_dict_to_group, groups))


def get_group(endpoint: str, username: str, password: str, group_id: str) -> Tuple[Optional[Group], List[Group]]:
    groups = get_groups(endpoint, username, password)
    for group in groups:
        if group.gid == group_id:
            return group, groups
    return None, groups


def get_unread_items_by_iid_ascending(endpoint: str, username: str, password: str, count: int, from_iid_exclusive: Optional[str], feed_filter: FeedFilter) -> List[Item]:
    api_key = fever_get_api_key(username, password)
    
    groups, feeds_groups = _get_groups(endpoint, username, password)
    group_by_id = {group['id']: group for group in groups}
    groups_by_feed_id = {}
    for feeds_group in feeds_groups:
        group_id = feeds_group['group_id']
        for feed_id in feeds_group['feed_ids'].split(','):
            if feed_id not in groups_by_feed_id:
                groups_by_feed_id[feed_id] = []
            groups_by_feed_id[feed_id].append(group_by_id[group_id])

    unread_item_ids_res = requests.post(endpoint + '/?api&unread_item_ids', data={'api_key': api_key})
    unread_item_ids_res.raise_for_status()
    unread_item_ids = unread_item_ids_res.json()['unread_item_ids']
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
        items_res = requests.post(f'{endpoint}/?api&items&since_id={since_id}', data={'api_key': api_key})
        items_res.raise_for_status()
        items = items_res.json()['items']
        if len(items) == 0:
            break
        batch_items = []
        for item in items:
            item_groups = groups_by_feed_id.get(str(item['feed_id']), [])
            batch_items.append(_item_dict_to_item(item, item_groups))
        batch_unread_items = []
        encountered_any_unread_item = False
        for item in batch_items:
            is_unread = int(item.iid) in unread_item_ids
            is_after = not feed_filter.created_after_seconds or feed_filter.created_after_seconds < item.created_timestamp_seconds
            is_group = not feed_filter.group_id or feed_filter.group_id in [group.gid for group in item.groups]
            if is_unread:
                encountered_any_unread_item = True
                unread_item_id_index += 1
            if is_unread and is_after and is_group:
                batch_unread_items.append(item)
        batch_unread_items = batch_unread_items[:count - len(unread_items)]
        if not encountered_any_unread_item:
            unread_item_id_index += 1
        unread_items += batch_unread_items

    return unread_items


def mark_items_as_read(endpoint: str, username: str, password: str, to_iid_inclusive: Optional[str], feed_filter: FeedFilter) -> int:
    mark_as_read_item_ids = []
    for image in get_images(endpoint, username, password, after, group_id):
        item_id = uid_to_item_id(image.uid)
        if min_item_id <= item_id <= max_item_id:
            mark_as_read_item_ids.append(item_id)

    api_key = fever_get_api_key(username, password)
    for item_id in mark_as_read_item_ids:
        mark_res = requests.post(endpoint + '/?api&mark=item&as=read&id=' + item_id, data={'api_key': api_key})
        mark_res.raise_for_status()

    return len(mark_as_read_item_ids)
