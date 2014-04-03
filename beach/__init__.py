import os
import json
import pipes
import re
import signal

import spur

from . import layouts, supervisors


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
    def __init__(self, registry, layout, supervisor):
        self._registry = registry
        self._layout = layout
        self._supervisor = supervisor
    
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
        self._supervisor.install()
        self._supervisor.set_up(service_name, cwd=app_path, username=username, command=command)
        
    
    def _read_app_config(self, path):
        with open(os.path.join(path, "beach.json")) as beach_config_file:
            beach_config = json.load(beach_config_file)
        return beach_config
