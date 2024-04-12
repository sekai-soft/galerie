import requests
import hashlib
import copy
from typing import List

ITEMS_QUERY_MAX_ITERS = 50


class FeverAuthError(Exception):
    pass


def fever_auth(endpoint: str, username: str, password: str) -> str:
    username_plus_password = username + ':' + password
    api_key = hashlib.md5(username_plus_password.encode()).hexdigest()

    auth_res = requests.post(endpoint + '/?api', data={'api_key': api_key})
    auth_res.raise_for_status()
    auth_res = auth_res.json()
    if 'auth' not in auth_res or auth_res['auth'] != 1:
        raise FeverAuthError()
    return api_key


def get_unread_items(endpoint: str, username: str, password: str) -> List[dict]:
    api_key = fever_auth(endpoint, username, password)
    
    groups_res = requests.post(endpoint + '/?api&groups', data={'api_key': api_key})
    groups_res.raise_for_status()
    groups = groups_res.json()['groups']
    group_by_id = {group['id']: group for group in groups}
    groups_by_feed_id = {}
    for feeds_groups in groups_res.json()['feeds_groups']:
        group_id = feeds_groups['group_id']
        for feed_id in feeds_groups['feed_ids'].split(','):
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
                item_with_group = copy.deepcopy(item)
                item_with_group['groups'] = groups_by_feed_id.get(str(item['feed_id']), [])
                unread_items.append(item_with_group)
        since_id = max([i['id'] for i in items])
    # unread_items is ordered by oldest first
    return list(reversed(unread_items))


def mark_items_as_read(endpoint: str, username: str, password: str, item_ids: int):
    api_key = fever_auth(endpoint, username, password)

    for item_id in item_ids:
        mark_res = requests.post(endpoint + '/?api&mark=item&as=read&id=' + item_id, data={'api_key': api_key})
        mark_res.raise_for_status()
