import os
import tempfile
import tarfile
import shutil

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
