import errno
import os
import tempfile
import tarfile
import shutil
import subprocess

from nose.tools import istest, assert_equal

from beach import tarballs


@istest
def temporary_tarball_contains_files_in_directory():
    dir_path = tempfile.mkdtemp()
    try:
        path = os.path.join(dir_path, "hello")
        os.mkdir(path)
        with open(os.path.join(path, "message"), "w") as message_file:
            message_file.write("Greetings!")
        
        with tarballs.create_temp_tarball(path) as tarball:
            tarball_reader = tarfile.open(name=tarball.name)
            message_file = tarball_reader.extractfile("hello/message")
            assert_equal("Greetings!", message_file.read())
        
    finally:
        shutil.rmtree(dir_path)


@istest
def can_create_temporary_tarball_using_path_with_trailing_slash():
    dir_path = tempfile.mkdtemp()
    try:
        path = os.path.join(dir_path, "hello")
        os.mkdir(path)
        with open(os.path.join(path, "message"), "w") as message_file:
            message_file.write("Greetings!")
        
        with tarballs.create_temp_tarball(path + "/") as tarball:
            tarball_reader = tarfile.open(name=tarball.name)
            message_file = tarball_reader.extractfile("hello/message")
            assert_equal("Greetings!", message_file.read())
        
    finally:
        shutil.rmtree(dir_path)



@istest
def temporary_tarball_ignores_files_according_to_gitignore():
    temp_dir = tempfile.mkdtemp()
    try:
        path = os.path.join(temp_dir, "repo")
        os.mkdir(path)
        _create_git_repo(
            path=path,
            filenames=["a", "b/a"],
            gitignore="/a"
        )
        
        with tarballs.create_temp_tarball(path) as tarball:
            tarball_reader = tarfile.open(name=tarball.name)
            assert_equal(set(["repo/.gitignore", "repo/b/a"]), set(tarball_reader.getnames()))
    finally:
        shutil.rmtree(temp_dir)

def _create_files(parent_path, filenames):
    for filename in filenames:
        path = os.path.join(parent_path, filename)
        _mkdir_p(os.path.dirname(path))
        with open(path, "w") as target:
            target.write("")

def _create_git_repo(path, filenames, gitignore):
    _create_files(path, filenames)
    with open(os.path.join(path, ".gitignore"), "w") as gitignore_file:
        gitignore_file.write(gitignore)
    subprocess.check_call(["git", "init"], cwd=path)


def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
