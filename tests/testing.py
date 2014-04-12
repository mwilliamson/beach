import os

import requests

from . import wait


def example_app_path(name):
    return os.path.join(os.path.dirname(__file__), "../example-apps", name)


def retry_http_get(address, timeout):
    return wait.retry(
        lambda: requests.get(address),
        error=requests.ConnectionError,
        timeout=timeout,
    )
