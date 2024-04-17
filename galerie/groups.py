from typing import List, Optional, Tuple
from dataclasses import dataclass
from .fever import fever_get_api_key, get_groups as fever_get_groups


@dataclass
class Group:
    title: str
    gid: str


def get_groups(fever_endpoint: str, fever_username: str, fever_password: str) -> List[Group]:
    api_key = fever_get_api_key(fever_username, fever_password)
    groups, _ = fever_get_groups(fever_endpoint, api_key)
    # the str(group['id']) is Fever API specific because Fever API's group IDs are int's but in other places group ID is str
    return [Group(title=group['title'], gid=str(group['id'])) for group in groups]


def get_group(fever_endpoint: str, fever_username: str, fever_password: str, group_id: str) -> Tuple[Optional[Group], List[Group]]:
    groups = get_groups(fever_endpoint, fever_username, fever_password)
    for group in groups:
        if group.gid == group_id:
            return group, groups
    return None, groups
