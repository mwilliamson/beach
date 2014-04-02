import contextlib
import os

from nose.tools import istest, nottest, assert_equal
import funk
import peachtree
import spur
import starboard
import requests

import beach


_local = spur.LocalShell()

@nottest
class BeachTests(object):
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
    
    @istest
    def can_use_vm(self):
        # Testing our test infrastructure
        with self._start_vm() as machine:
            shell = machine.shell()
            result = shell.run(["echo", "hello"])
            assert_equal("hello\n", result.output)
    
    @istest
    def can_run_standalone_script(self):
        deployer = beach.Deployer(_local, registry=None)
        app_path = os.path.join(os.path.dirname(__file__), "../example-apps/just-a-script")
        with deployer.run(app_path, params={"port": "58080"}):
            # TODO: remove sleep
            import time
            time.sleep(1)
            response = requests.get("http://localhost:58080")
            assert_equal("Hello", response.text)
    
    @istest
    @funk.with_mocks
    def can_run_script_with_dependency(self, mocks):
        registry = mocks.mock()
        node_service = Service({"value": "I feel fine"})
        funk.allows(registry).find_service("message").returns(node_service)
            
        deployer = beach.Deployer(_local, registry=registry)
        app_path = os.path.join(os.path.dirname(__file__), "../example-apps/script-with-dependency")
        with deployer.run(app_path, params={"port": "58080"}):
            # TODO: remove sleep
            import time
            time.sleep(1)
            response = requests.get("http://localhost:58080")
            assert_equal("I feel fine", response.text)
    
    @istest
    def can_deploy_standalone_script(self):
        with self._start_vm(public_ports=[8080]) as machine:
            deployer = beach.Deployer(machine.root_shell(), registry=None)
            app_path = os.path.join(os.path.dirname(__file__), "../example-apps/just-a-script")
            deployer.deploy(app_path, params={"port": "8080"})
            address = "http://{0}:{1}".format(machine.external_hostname(), machine.public_port(8080))
            # TODO: remove sleep
            import time
            time.sleep(5)
            response = requests.get(address)
            assert_equal("Hello", response.text)


class Service(object):
    def __init__(self, provides):
        self.provides = provides


@istest
class BeachPrecise64Tests(BeachTests):
    image_name = "ubuntu-precise-amd64"
