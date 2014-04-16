import os
import posixpath
import contextlib
import uuid
import shutil
import tempfile
import subprocess
import hashlib
import time

import spur
import tempman

from . import contexts

_local = spur.LocalShell()


class TemporaryLayout(contexts.Closeable):
    def __init__(self):
        self._dir = tempman.create_temp_dir()
        self.run = _local.run
    
    def close(self):
        self._dir.close()
    
    def upload_service(self, service_name, path):
        destination = os.path.join(self._dir.path, service_name)
        subprocess.check_call(["cp", "-rT", path, destination])
        return destination, None


class UserPerService(contexts.Closeable):
    def __init__(self, shell):
        self._shell = shell
        self.run = shell.run
    
    def close(self):
        pass
    
    def upload_service(self, service_name, path):
        self._create_user_if_missing(service_name)
        
        with self._create_temp_tarball(path) as local_tarball:
            service_hash = _file_hash(local_tarball)
            local_tarball.seek(0)
            
            home_path = self._shell.run(["su", service_name, "-", "-c" "sh -c 'echo $HOME'"]).output.strip()
            app_path = self._path_join(home_path, "{0}-{1}".format(int(time.time()), service_hash[:10]))
            self._shell.run(["mkdir", "-p", app_path])
            
            self._upload_tarball(local_tarball, app_path)
        
        return app_path, service_name
        
    def _create_user_if_missing(self, username):
        if self._shell.run(["id", username], allow_error=True).return_code != 0:
            self._shell.run(["adduser", "--disabled-password", "--gecos", "", username])
    
    def _upload_tarball(self, local_tarball, remote_path):
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
    
    @contextlib.contextmanager
    def _create_temp_tarball(self, path):
        with tempfile.NamedTemporaryFile() as tarball:
            subprocess.check_call(
                ["tar", "czf", tarball.name, os.path.basename(path)],
                cwd=os.path.dirname(path),
            )
            yield tarball
    
    def _path_join(self, *args):
        return posixpath.join(*args)


def _file_hash(fileobj):
    hasher = hashlib.sha1()
    while True:
        data = fileobj.read(8192)
        if not data:
            break
        hasher.update(data)
    return hasher.hexdigest()
