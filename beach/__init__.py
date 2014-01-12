import subprocess
import posixpath
import os
import json
import tempfile
import contextlib
import shutil
import uuid


class Deployer(object):
    def __init__(self, shell):
        self._shell = shell
    
    def deploy(self, path, params):
        app_config = self._read_app_config(path)
        app_name = app_config["name"]
        home_path = self._shell.run(["sh", "-c", "echo $PATH"]).output.strip()
        app_path = self._path_join(home_path, "beach-apps", app_name)
        self._shell.run(["mkdir", "-p", app_path])
        
        self._upload_dir(path, app_path)
        
        self._set_up_service(app_config, app_path, params)
    
    def _upload_dir(self, local_path, remote_path):
        with self._create_temp_tarball(local_path) as local_tarball:
            # TODO: hash file to get name
            remote_tarball_path = os.path.join("/tmp", str(uuid.uuid4()))
            with self._shell.open(remote_tarball_path, "w") as remote_tarball:
                shutil.copyfileobj(local_tarball, remote_tarball)
        
        self._shell.run(["mkdir", "-p", remote_path])
        self._shell.run(
            [
                "tar", "xzf", remote_tarball_path,
                "--strip-components=1",
            ],
            cwd=remote_path,
        )
        self._shell.run(["rm", remote_tarball_path])
    
    def _set_up_service(self, app_config, app_path, params):
        supervisor = RunitSupervisor(self._shell)
        supervisor.install()
        service_name = "beach-{0}".format(app_config["name"])
        # TODO: read params from app config
        # TODO: run as less privileged user
        command = app_config["command"]
        supervisor.set_up(service_name, env=params, cwd=app_path, command=command)
    
    @contextlib.contextmanager
    def _create_temp_tarball(self, path):
        with tempfile.NamedTemporaryFile() as tarball:
            subprocess.check_call(
                ["tar", "czf", tarball.name, os.path.basename(path)],
                cwd=os.path.dirname(path),
            )
            yield tarball
        
    
    def _read_app_config(self, path):
        with open(os.path.join(path, "beach.json")) as beach_config_file:
            beach_config = json.load(beach_config_file)
        return beach_config
    
    def _path_join(self, *args):
        return posixpath.join(*args)


class RunitSupervisor(object):
    def __init__(self, shell):
        self._shell = shell
    
    def install(self):
        self._shell.run(["apt-get", "install", "runit", "-y"])
    
    def set_up(self, service_name, env, cwd, command):
        service_path = "/etc/sv/{0}".format(service_name)
        service_run_path = os.path.join(service_path, "run")
        # TODO: escape single quote marks
        env_update = "\n".join(
            "{0}='{1}'".format(key, value)
            for key, value in env.items()
        )
        run_contents = "#!/usr/bin/env sh\n\nset -e\n{0}\ncd '{1}';exec {2}".format(env_update, cwd, command)
        self._write_remote_file(service_run_path, run_contents)
        self._shell.run(["chmod", "+x", service_run_path])
        self._shell.run(["ln", "-sfT", service_path, "/etc/service/{0}".format(service_name)])
    
    def _write_remote_file(self, path, contents):
        self._shell.run(["mkdir", "-p", os.path.dirname(path)])
        with self._shell.open(path, "w") as remote_file:
            remote_file.write(contents)
        
