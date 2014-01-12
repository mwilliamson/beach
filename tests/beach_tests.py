import contextlib
import pipes
import os

from nose.tools import istest, nottest, assert_equal
import spur
import tempman


_local = spur.LocalShell()

@nottest
class BeachTests(object):
    @contextlib.contextmanager
    def _start_vm(self):
        with tempman.create_temp_dir() as temp_dir:
            machine = VagrantMachine(self.box_name, temp_dir.path)
            machine.start()
            yield machine
    
    @istest
    def can_use_vm(self):
        # Testing our test infrastructure
        with self._start_vm() as machine:
            result = machine.run(["echo", "hello"])
            assert_equal("hello\n", result.output)


class VagrantMachine(object):
    def __init__(self, box_name, machine_dir):
        self._box_name = box_name
        self._machine_dir = machine_dir
    
    def start(self):
        self._vagrant("init", self._box_name)
        self._vagrant("up")
    
    def destroy(self):
        self._vagrant("destroy")
    
    def run(self, command):
        command_str = " ".join(map(pipes.quote, command))
        return self._vagrant("ssh", "-c", command_str)
    
    def _vagrant(self, *args):
        return _local.run(["vagrant"] + list(args), cwd=self._machine_dir)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.destroy()


@istest
class BeachPrecise32Tests(BeachTests):
    box_name = "precise32"


@istest
class BeachPrecise64Tests(BeachTests):
    box_name = "precise64"


@istest
class BeachWheezy64Tests(BeachTests):
    box_name = "wheezy64"
