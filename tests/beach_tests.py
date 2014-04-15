from nose.tools import istest, nottest, assert_equal, assert_raises
from nose.plugins.attrib import attr
import funk
import spur
import requests

import beach
from . import testing


_local = spur.LocalShell()


@nottest
class BeachTests(object):
    def __init__(self):
        self._cleanup = []
    
    def add_cleanup(self, *cleanup):
        self._cleanup.extend(cleanup)
    
    def setup(self):
        self.layout = self.create_layout()
        self.supervisor = self.create_supervisor()
        self.registry = self.create_registry()
        self.add_cleanup(self.layout.close, self.supervisor.close)
        
    def teardown(self):
        while len(self._cleanup) > 0:
            self._cleanup.pop()()
        
    def deployer(self):
        return beach.Deployer(
            registry=self.registry,
            layout=self.layout,
            supervisor=self.supervisor,
        )
    
    @istest
    def can_deploy_standalone_script(self):
        deployer = self.deployer()
        app_path = testing.example_app_path("just-a-script")
        deployer.deploy(app_path, params={"port": "58080"})
        response = self._retry_http_get(port=58080, path="/")
        assert_equal("Hello", response.text)
            
    @istest
    def can_deploy_script_with_installation(self):
        deployer = self.deployer()
        app_path = testing.example_app_path("script-with-install")
        deployer.deploy(app_path, params={"port": "58080"})
        response = self._retry_http_get(port=58080, path="/")
        assert_equal("I feel fine\n", response.text)
    
    @istest
    @funk.with_mocks
    def can_deploy_script_with_dependency(self, mocks):
        self.registry.register("message", provides={"value": "I feel fine"})
        deployer = self.deployer()
        app_path = testing.example_app_path("script-with-dependency")
        deployer.deploy(app_path, params={"port": "58080"})
        response = self._retry_http_get(port=58080, path="/")
        assert_equal("I feel fine", response.text)
    
    @istest
    def redeploying_restarts_service(self):
        deployer = self.deployer()
        app_path = testing.example_app_path("just-a-script")
        
        deployer.deploy(app_path, params={"port": "58080"})
        response = self._retry_http_get(port=58080, path="/")
        assert_equal("Hello", response.text)
        
        deployer.deploy(app_path, params={"port": "58081"})
        response = self._retry_http_get(port=58081, path="/")
        assert_equal("Hello", response.text)
        assert_raises(requests.ConnectionError, lambda: requests.get(self.http_address(58080, "/")))
    
    def _retry_http_get(self, port, path):
        address = self.http_address(port=port, path=path)
        return testing.retry_http_get(address, timeout=self.http_timeout)


@istest
class TemporaryDeploymentTests(BeachTests):
    http_timeout = 1
    
    def create_supervisor(self):
        return beach.supervisors.stop_on_exit()
    
    def create_layout(self):
        return beach.layouts.TemporaryLayout()
    
    def create_registry(self):
        return beach.registries.InMemoryRegistry()
    
    def http_address(self, port, path):
        return "http://localhost:{0}{1}".format(port, path)


@attr("slow")
@nottest
class ProductionDeploymentTests(BeachTests):
    http_timeout = 5
    
    def __init__(self):
        super(ProductionDeploymentTests, self).__init__()
        self._machine = self._start_vm(public_ports=[58080, 58081])
        self.add_cleanup(self._machine.destroy)
    
    def create_supervisor(self):
        return beach.supervisors.runit(self._machine.root_shell())
    
    def create_layout(self):
        return beach.layouts.UserPerService(self._machine.root_shell())
    
    def create_registry(self):
        return beach.registries.FileRegistry(
            self._machine.root_shell(),
            "/root/beach-registry.json",
        )
    
    @istest
    def can_use_vm(self):
        # Testing our test infrastructure
        shell = self._machine.shell()
        result = shell.run(["echo", "hello"])
        assert_equal("hello\n", result.output)
        
        
    def http_address(self, port, path):
        return "http://{0}:{1}{2}".format(
            self._machine.external_hostname(),
            self._machine.public_port(port),
            path,
        )
    
    def _start_vm(self, **kwargs):
        return testing.start_vm(self.image_name, **kwargs)


@istest
class ProductionDeploymentPrecise64Tests(ProductionDeploymentTests):
    image_name = "ubuntu-precise-amd64"

