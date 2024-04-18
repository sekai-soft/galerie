import requests
import hashlib
from typing import List, Tuple, Optional
from .item import Item
from .group import Group
from .image import extract_images, Image, uid_to_item_id

ITEMS_QUERY_MAX_ITERS = 50


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


def get_groups(endpoint: str, username: str, password: str):
    groups, _ = _get_groups(endpoint, username, password)
    return list(map(_group_dict_to_group, groups))


def get_group(endpoint: str, username: str, password: str, group_id: str) -> Tuple[Optional[Group], List[Group]]:
    groups = get_groups(endpoint, username, password)
    for group in groups:
        if group.gid == group_id:
            return group, groups
    return None, groups


def _get_unread_items(endpoint: str, username: str, password: str) -> List[Item]:
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
    unread_item_ids = list(map(int, unread_item_ids.split(',')))
    # &items&since_id query looks like it's exclusive, e.g. since_id's item will not be included
    # hence need to -1 to make sure since_id's item is also included
    since_id = min(unread_item_ids) - 1

    unread_items = []
    for _ in range(ITEMS_QUERY_MAX_ITERS):
        items_res = requests.post(endpoint + '/?api&items&since_id=' + str(since_id), data={'api_key': api_key})
        items_res.raise_for_status()
        items = items_res.json()['items']
        if len(items) == 0:
            break
        for item in items:
            if item['id'] in unread_item_ids:
                item_groups = groups_by_feed_id.get(str(item['feed_id']), [])
                unread_items.append(Item(
                    created_timestamp_seconds=item['created_on_time'],
                    html=item['html'],
                    # the str casting here is Fever API specific because Fever API's IDs are int's but str is required
                    iid=str(item['id']),
                    url=item['url'],
                    groups=list(map(_group_dict_to_group, item_groups)),
                ))
        since_id = max([i['id'] for i in items])
    # unread_items is ordered by oldest first
    return list(reversed(unread_items))


def get_images(endpoint: str, username: str, password: str, after: Optional[int], group_id: Optional[str]) -> List[Image]:
    images = []
    for item in _get_unread_items(endpoint, username, password):
        should_include_for_after = not after or after < item.created_timestamp_seconds
        should_include_for_group = not group_id or group_id in [group.gid for group in item.groups]
        if should_include_for_after and should_include_for_group:
            html = item.html
            images += extract_images(html, item)
    return images


def mark_items_as_read(endpoint: str, username: str, password: str, after: Optional[int], group_id: Optional[str], session_max_uid: str, min_uid: str) -> int:
    max_item_id = uid_to_item_id(session_max_uid)
    min_item_id = uid_to_item_id(min_uid)

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
