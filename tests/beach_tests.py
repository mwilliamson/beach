import contextlib
import os

from nose.tools import istest, nottest, assert_equal
import peachtree
import spur
import starboard


_local = spur.LocalShell()

@nottest
class BeachTests(object):
    def _start_vm(self):
        provider = peachtree.qemu_provider()
        machine = provider.start(self.image_name)
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
class BeachPrecise64Tests(BeachTests):
    image_name = "ubuntu-precise-amd64"
