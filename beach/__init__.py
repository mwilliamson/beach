import subprocess
import posixpath
import os
import json
import tempfile
import contextlib
import shutil
import uuid
import pipes


class Deployer(object):
    def __init__(self, shell):
        self._shell = shell
    
    def deploy(self, path, params):
        app_config = self._read_app_config(path)
        service_name = "beach-{0}".format(app_config["name"])
        self._create_user_if_missing(service_name)
        app_name = app_config["name"]
        home_path = self._shell.run(["su", service_name, "-", "-c" "sh -c 'echo $HOME'"]).output.strip()
        app_path = self._path_join(home_path, "beach-apps", app_name)
        self._shell.run(["mkdir", "-p", app_path])
        
        self._upload_dir(path, app_path)
        
        self._set_up_service(service_name, app_config, app_path, params)
    
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
    
    def _set_up_service(self, service_name, app_config, app_path, params):
        supervisor = Supervisor(self._shell, os.path.join("shell/supervisors/runit"))
        supervisor.install()
        # TODO: read params from app config
        command = app_config["service"]
        supervisor.set_up(service_name, env=params, cwd=app_path, command=command)
        
    def _create_user_if_missing(self, username):
        if self._shell.run(["id", username], allow_error=True).return_code != 0:
            self._shell.run(["adduser", "--disabled-password", "--gecos", "", username])
    
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


class Supervisor(object):
    def __init__(self, shell, scripts_dir):
        self._shell = shell
        self._scripts_dir = scripts_dir
    
    def install(self):
        self._run_script("install")
    
    def set_up(self, service_name, env, cwd, command):
        env_update = "\n".join(
            "{0}={1}".format(key, pipes.quote(value))
            for key, value in env.items()
        )
        exec_command = "set -e\n{0}\ncd {1}\nexec {2}".format(
            env_update, pipes.quote(cwd), command)
        full_command = "set -e\nexec su {0} - -c sh -c {1}".format(
            service_name, pipes.quote(exec_command))
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
