import contextlib
import tempfile
import os
import subprocess

import mayo


@contextlib.contextmanager
def create_temp_tarball(path):
    path = os.path.normpath(path)
    
    with tempfile.NamedTemporaryFile() as tarball:
        filenames = [
            os.path.join(os.path.basename(path), filename)
            for filename in _filenames(path)
        ]
        subprocess.check_call(
            ["tar", "czf", tarball.name] + filenames,
            cwd=os.path.dirname(path),
        )
        yield tarball


def _filenames(path):
    repository = mayo.repository_at(path)
    if repository is not None and repository.type == "git":
        return _git_filenames(repository)
    else:
        return _all_filenames(path)


def _git_filenames(repository):
    ignored_files = repository.find_ignored_files()
    
    for filename in _all_filenames(repository.working_directory):
        if filename not in ignored_files and not filename.startswith(".git/"):
            yield filename
    


def _all_filenames(path):
    result = []
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            yield os.path.relpath(full_path, path)
