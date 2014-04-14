import spur
import tempfile
from nose.tools import istest, nottest, assert_equal

from beach import registries


@nottest
class RegistryTests(object):
    @istest
    def find_service_is_none_if_no_such_service_exists(self):
        assert_equal(None, self.registry.find_service("node-0.10"))
    
    @istest
    def can_find_service_after_registration(self):
        provides = {"version": "0.10.2"}
        self.registry.register("node-0.10", provides=provides)
        assert_equal(provides, self.registry.find_service("node-0.10").provides)
    
    @istest
    def existing_entries_are_not_destroyed_by_registration(self):
        self.registry.register("node-0.10", provides={})
        self.registry.register("node-0.8", provides={})
        assert self.registry.find_service("node-0.10") is not None
    
    @istest
    def cannot_find_service_after_deregistration(self):
        self.registry.register("node-0.10", provides={})
        assert self.registry.find_service("node-0.10") is not None 
        self.registry.deregister("node-0.10")
        assert self.registry.find_service("node-0.10") is None


@istest
class InMemoryRegistryTests(RegistryTests):
    def setup(self):
        self.registry = registries.InMemoryRegistry()


@istest
class FileRegistryTests(RegistryTests):
    def setup(self):
        self._registry_file = tempfile.NamedTemporaryFile("w")
        self.registry = registries.FileRegistry(spur.LocalShell(), self._registry_file.name)
    
    def teardown(self):
        self._registry_file.close()
    
    @istest
    def error_if_registry_file_is_badly_formatted(self):
        self._registry_file.write("!!!")
        self._registry_file.flush()
        try:
            self.registry.find_service("node-0.10")
            assert False, "Expected ValueError"
        except ValueError as error:
            assert_equal("Registry file was not valid JSON", str(error))
