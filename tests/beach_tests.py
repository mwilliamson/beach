import contextlib
import os

from nose.tools import istest, nottest, assert_equal, assert_raises
from nose.plugins.attrib import attr
import funk
import peachtree
import spur
import starboard
import requests

import beach
from . import wait


_local = spur.LocalShell()

@istest
class BeachTests(object):
    @istest
    def can_run_standalone_script(self):
        deployer = beach.Deployer(registry=None, layout=None, supervisor=None)
        app_path = _example_app_path("just-a-script")
        with deployer.run(app_path, params={"port": "58080"}):
            response = self._retry_http_get("http://localhost:58080")
            assert_equal("Hello", response.text)
    
    @istest
    @funk.with_mocks
    def can_run_script_with_dependency(self, mocks):
        registry = mocks.mock()
        node_service = Service({"value": "I feel fine"})
        funk.allows(registry).find_service("message").returns(node_service)
            
        deployer = beach.Deployer(registry=registry, layout=None, supervisor=None)
        app_path = _example_app_path("script-with-dependency")
        with deployer.run(app_path, params={"port": "58080"}):
            response = self._retry_http_get("http://localhost:58080")
            assert_equal("I feel fine", response.text)
    
    def _retry_http_get(self, address):
        return _retry_http_get(address, timeout=1)


def _retry_http_get(address, timeout):
    return wait.retry(
        lambda: requests.get(address),
        error=requests.ConnectionError,
        timeout=timeout,
    )


@attr("slow")
@nottest
class BeachDeploymentTests(object):
    @istest
    def can_use_vm(self):
        # Testing our test infrastructure
        with self._start_vm() as machine:
            shell = machine.shell()
            result = shell.run(["echo", "hello"])
            assert_equal("hello\n", result.output)
    
    @istest
    def can_deploy_standalone_script(self):
        with self._start_vm(public_ports=[8080]) as machine:
            shell = machine.root_shell()
            deployer = beach.Deployer(
                registry=None,
                layout=beach.layouts.UserPerService(shell),
                supervisor=beach.supervisors.runit(shell),
            )
            app_path = _example_app_path("just-a-script")
            deployer.deploy(app_path, params={"port": "8080"})
            address = self._address(machine, 8080)
            response = self._retry_http_get(address)
            assert_equal("Hello", response.text)
    
    @istest
    def redeploying_restarts_service(self):
        with self._start_vm(public_ports=[8080, 8081]) as machine:
            shell = machine.root_shell()
            deployer = beach.Deployer(
                registry=None,
                layout=beach.layouts.UserPerService(shell),
                supervisor=beach.supervisors.runit(shell),
            )
            app_path = _example_app_path("just-a-script")
            
            deployer.deploy(app_path, params={"port": "8080"})
            first_address = self._address(machine, 8080)
            response = self._retry_http_get(first_address)
            assert_equal("Hello", response.text)
            
            deployer.deploy(app_path, params={"port": "8081"})
            second_address = self._address(machine, 8081)
            response = self._retry_http_get(first_address)
            assert_equal("Hello", response.text)
            assert_raises(requests.ConnectionError, lambda: requests.get(second_address))
            
            
    def _address(self, machine, port):
        return "http://{0}:{1}".format(machine.external_hostname(), machine.public_port(port))
    
    def _start_vm(self, **kwargs):
        provider = peachtree.qemu_provider()
        machine = provider.start(self.image_name, **kwargs)
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
    
    def _retry_http_get(self, address):
        return _retry_http_get(address, timeout=5)


class Service(object):
    def __init__(self, provides):
        self.provides = provides


@istest
class BeachPrecise64Tests(BeachDeploymentTests):
    image_name = "ubuntu-precise-amd64"


def _example_app_path(name):
    return os.path.join(os.path.dirname(__file__), "../example-apps", name)

