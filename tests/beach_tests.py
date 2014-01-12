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
        return provider.start("ubuntu-precise-amd64")
    
    @istest
    def can_use_vm(self):
        # Testing our test infrastructure
        with self._start_vm() as machine:
            shell = machine.shell()
            result = shell.run(["echo", "hello"])
            assert_equal("hello\n", result.output)


#~ @istest
#~ class BeachPrecise32Tests(BeachTests):
    #~ box_name = "precise32"


@istest
class BeachPrecise64Tests(BeachTests):
    box_name = "ubuntu-precise-amd64"


#~ @istest
#~ class BeachWheezy64Tests(BeachTests):
    #~ box_name = "wheezy64"
