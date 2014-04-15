import os

import requests
import peachtree
import starboard

from . import wait


def example_app_path(name):
    return os.path.join(os.path.dirname(__file__), "../example-apps", name)


def retry_http_get(address, timeout):
    return wait.retry(
        lambda: requests.get(address),
        error=requests.ConnectionError,
        timeout=timeout,
    )

    
def start_vm(*args, **kwargs):
    provider = peachtree.qemu_provider()
    machine = provider.start(*args, **kwargs)
    try:
        root_shell = machine.root_shell()
        hostname = starboard.find_local_hostname()
        # TODO: verify apt-cacher-ng is running
        # TODO: verify that caching is working correctly
        apt_config = 'Acquire::http::Proxy "http://{0}:3142";\n'.format(hostname)
        with root_shell.open("/etc/apt/apt.conf.d/01-proxy-cache", "w") as config_file:
            config_file.write(apt_config)
        return machine
    except:
        machine.destroy()
        raise
