from typing import List
from dataclasses import dataclass
from .fever import fever_auth, get_groups as fever_get_groups


@dataclass
class Group:
    title: str
    gid: str


def get_groups(fever_endpoint: str, fever_username: str, fever_password: str) -> List[Group]:
    api_key = fever_auth(fever_endpoint, fever_username, fever_password)
    groups, _ = fever_get_groups(fever_endpoint, api_key)
    return [Group(title=group['title'], gid=str(group['id'])) for group in groups]
