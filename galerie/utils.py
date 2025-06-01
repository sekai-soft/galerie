import os


def get_base_url():
    if 'BASE_URL' not in os.environ:
        return ''
    base_url = os.environ['BASE_URL']
    if base_url.endswith('/'):
        return base_url[:-1]
    return base_url
