import os
import pipes
import signal

import spur

from . import contexts


def runit(shell):
    return _supervisor(shell, "runit")


def stop_on_exit():
    return StopOnExit()


class StopOnExit(contexts.Closeable):
    def __init__(self):
        self._processes = {}
    
    def close(self):
        for process in self._processes.values():
            self._kill(process)
    
    def install(self):
        pass
    
    def set_up(self, service_name, cwd, username, command):
        if username is None:
            existing_process = self._processes.get(service_name)
            if existing_process is not None:
                self._kill(existing_process)
            
            shell = spur.LocalShell()
            process = shell.spawn(
                ["sh", "-c", "exec {0}".format(command)],
                allow_error=True,
                cwd=cwd,
            )
            self._processes[service_name] = process
        else:
            raise ValueError("username must be None")
    
    def _kill(self, process):
        process.send_signal(signal.SIGTERM)
        process.wait_for_result()


def _supervisor(shell, name):
    path = os.path.join(os.path.dirname(__file__), "../shell/supervisors/", name)
    return Supervisor(shell, path)


class Supervisor(contexts.Closeable):
    def __init__(self, shell, scripts_dir):
        self._shell = shell
        self._scripts_dir = scripts_dir
    
    def close(self):
        pass
    
    def install(self):
        self._run_script("install")
    
    def set_up(self, service_name, cwd, username, command):
        assert username is not None
        exec_command = "set -e\ncd {0}\nexec {1}".format(
            pipes.quote(cwd), command)
        full_command = "set -e\nexec su {0} - -c sh -c {1}".format(
            username, pipes.quote(exec_command))
        self._run_script(
            "create-service",
            {"service_name": service_name, "command": full_command},
        )
    
    def _run_script(self, name, env={}):
        self._shell.run(["sh", "-c", self._read_script(name)], update_env=env)
    
    def _read_script(self, name):
        return _read_file(os.path.join(self._scripts_dir, name))
        

def _read_file(path):
    with open(path) as f:
        return f.read()
