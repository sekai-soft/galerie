import os


def get_base_url():
    if 'BASE_URL' not in os.environ:
        return ''
    base_url = os.environ['BASE_URL']
    if base_url.endswith('/'):
        return base_url[:-1]
    return base_url


def get_media_proxy_base_url() -> str:
    if 'MEDIA_PROXY_BASE_URL' not in os.environ:
        return ''
    media_proxy_base_url = os.environ['MEDIA_PROXY_BASE_URL']
    if media_proxy_base_url.endswith('/'):
        media_proxy_base_url = media_proxy_base_url[:-1]
    return media_proxy_base_url
