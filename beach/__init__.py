import posixpath
import os
import json
import pipes
import re
import signal

import spur

from . import layouts


_local = spur.LocalShell()


class RunningApplication(object):
    def __init__(self, process):
        self._process = process
    
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self._process.send_signal(signal.SIGTERM)
        self._process.wait_for_result()


class Deployer(object):
    def __init__(self, shell, registry, layout):
        self._shell = shell
        self._registry = registry
        self._layout = layout
    
    def run(self, path, params):
        app_config = self._read_app_config(path)
        command = self._generate_command(params, app_config)
        
        process = _local.spawn(
            ["sh", "-c", "exec {0}".format(command)],
            cwd=path,
            allow_error=True,
        )
        
        return RunningApplication(process)
    
    def deploy(self, path, params):
        app_config = self._read_app_config(path)
        command = self._generate_command(params, app_config)
        
        service_name = "beach-{0}".format(app_config["name"])
        
        app_path, username = self._layout.upload_service(service_name, path)
        
        self._set_up_service(service_name, app_path, username, command)
    
    def _generate_command(self, params, app_config):
        # TODO: Read params from app config to ensure all are satisfied.
        env = params.copy()
        for dependency_name in app_config.get("dependencies", []):
            service = self._registry.find_service(dependency_name)
            for key, value in service.provides.items():
                env["{0}.{1}".format(dependency_name, key)] = value
        
        
        command = app_config["service"]
        
        def replace_variable(matchobj):
            return pipes.quote(env[matchobj.group(1)])
        
        return re.sub(r"\$\{([^}]+)\}", replace_variable, command)
    
    def _set_up_service(self, service_name, app_path, username, command):
        supervisor = Supervisor(self._shell, os.path.join("shell/supervisors/runit"))
        supervisor.install()
        supervisor.set_up(service_name, cwd=app_path, username=username, command=command)
        
    
    def _read_app_config(self, path):
        with open(os.path.join(path, "beach.json")) as beach_config_file:
            beach_config = json.load(beach_config_file)
        return beach_config
    
    def _path_join(self, *args):
        return posixpath.join(*args)


class Supervisor(object):
    def __init__(self, shell, scripts_dir):
        self._shell = shell
        self._scripts_dir = scripts_dir
    
    def install(self):
        self._run_script("install")
    
    def set_up(self, service_name, cwd, username, command):
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
