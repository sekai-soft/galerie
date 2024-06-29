import responses
from .fever_aggregator import FeverAggregator
from .feed_filter import FeedFilter


def consecutive_items(from_index_inclusive: int, to_index_exclusive: int):
    return [
        {"id": i, "created_on_time": i, "html": f"html{i}", "url": f"url{i}", "feed_id": 1}
        for i in range(from_index_inclusive, to_index_exclusive)
    ]


@responses.activate
def test_get_unread_items_by_iid_ascending():
    endpoint = "http://fever"
    fever_aggregator = FeverAggregator(endpoint, "username", "password", False)
    count = 5
    unread_item_ids = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]
    unread_item_ids = list(map(str, unread_item_ids))

    # groups and unread_item_ids responses
    groups_resp = responses.Response(method=responses.POST,
        url=f"{endpoint}/?api&groups",
        status=200,
        json={
            "groups": [
                {"id": 1, "title": "Group 1"}],
            "feeds_groups": [
                {"group_id": 1, "feed_ids": "1"}]
        })
    unread_item_ids_resp = responses.Response(
        method=responses.POST,
        url=f"{endpoint}/?api&unread_item_ids",
        status=200,
        json={"unread_item_ids": ",".join(unread_item_ids)})

    # call 1
    responses.add(groups_resp)
    responses.add(unread_item_ids_resp)
    responses.add(
        method=responses.POST,
        url=f"{endpoint}/?api&items&since_id=0",
        status=200,
        json={"items": consecutive_items(1, 6)})

    # call 2
    responses.add(groups_resp)
    responses.add(unread_item_ids_resp)
    responses.add(
        method=responses.POST,
        url=f"{endpoint}/?api&items&since_id=5",
        status=200,
        json={"items": consecutive_items(6, 11)})
    
    # call 3
    responses.add(groups_resp)
    responses.add(unread_item_ids_resp)
    responses.add(
        method=responses.POST,
        url=f"{endpoint}/?api&items&since_id=10",
        status=200,
        json={"items": consecutive_items(11, 13)})

    unread_items = []
    items = fever_aggregator.get_unread_items_by_iid_ascending(
        count=count,
        from_iid_exclusive=None,
        feed_filter=FeedFilter(None, None))
    unread_items += items
    while items:
        items = fever_aggregator.get_unread_items_by_iid_ascending(
            count=count,
            from_iid_exclusive=items[-1].iid,
            feed_filter=FeedFilter(None, None))
        unread_items += items
    assert list(map(lambda item: item.iid, unread_items)) == unread_item_ids
