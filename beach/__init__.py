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
        self._upload_dir(path)
    
    def _upload_dir(self, path):
        with self._create_temp_tarball(path) as app_tarball:
            app_config = self._read_app_config(path)
            app_name = app_config["name"]
            home_path = self._shell.run(["sh", "-c", "echo $PATH"]).output.strip()
            app_path = self._path_join(home_path, "beach-apps", app_name)
            self._shell.run(["mkdir", "-p", app_path])
            
            # TODO: hash file to get name
            remote_app_tarball_path = os.path.join(home_path, str(uuid.uuid4()))
            with self._shell.open(remote_app_tarball_path, "w") as remote_app_tarball:
                shutil.copyfileobj(app_tarball, remote_app_tarball)
            
        self._shell.run(
            [
                "tar", "xzf", remote_app_tarball_path,
                "--strip-components=1",
            ],
            cwd=app_path,
        )
        print self._shell.run(["ls", "-a"], cwd=app_path).output
        # TODO: use runit
        self._shell.spawn(
            ["sh", "-c", app_config["command"]],
            update_env={"PORT": "8080"},
            cwd=app_path,
        )
    
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


class WrappedStdin(object):
    def __init__(self, process):
        self._process = process
