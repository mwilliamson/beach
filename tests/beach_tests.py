import contextlib
import os

from nose.tools import istest, nottest, assert_equal
import peachtree
import spur


_local = spur.LocalShell()

@nottest
class BeachTests(object):
    def _start_vm(self):
        provider = peachtree.qemu_provider()
        return provider.start(self.image_name)
    
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
