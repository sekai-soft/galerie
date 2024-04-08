import requests
import hashlib
from typing import List

ITEMS_QUERY_MAX_ITERS = 50


def get_unread_items(endpoint: str, username: str, password: str) -> List[dict]:
    username_plus_password = username + ':' + password
    api_key = hashlib.md5(username_plus_password.encode()).hexdigest()

    auth_res = requests.post(endpoint + '/?api', data={'api_key': api_key})
    auth_res.raise_for_status()
    auth_res = auth_res.json()
    if 'auth' not in auth_res or auth_res['auth'] != 1:
        raise RuntimeError('Authentication failed')

    unread_item_ids_res = requests.post(endpoint + '/?api&unread_item_ids', data={'api_key': api_key})
    unread_item_ids_res.raise_for_status()
    unread_item_ids = list(map(int, unread_item_ids_res.json()['unread_item_ids'].split(',')))
    if len(unread_item_ids) == 0:
        return []
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
                unread_items.append(item)
        since_id = max([i['id'] for i in items])
    # unread_items is ordered by oldest first
    return list(reversed(unread_items))
