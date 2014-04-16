import contextlib
import tempfile
import os
import subprocess


@contextlib.contextmanager
def create_temp_tarball(path):
    with tempfile.NamedTemporaryFile() as tarball:
        subprocess.check_call(
            ["tar", "czf", tarball.name, os.path.basename(path)],
            cwd=os.path.dirname(path),
        )
        yield tarball
