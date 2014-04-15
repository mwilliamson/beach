import tempfile
import signal
import json

import spur
from nose.tools import istest, assert_equal

from . import testing
import beach

_local = spur.LocalShell()


@istest
def can_deploy_temporarily_using_cli():
    app_path = testing.example_app_path("just-a-script")
    # TODO: allow integer parameters
    params = {"port": "58080"}
    config = {"params": params}
    
    with tempfile.NamedTemporaryFile() as config_file:
        json.dump(config, config_file)
        config_file.flush()
    
        process = _local.spawn([
            "beach", "deploy",
            app_path,
            "-c", config_file.name
        ])
        try:
            response = testing.retry_http_get("http://localhost:58080", timeout=1)
            assert_equal("Hello", response.text)
        finally:
            process.send_signal(signal.SIGINT)
            process.wait_for_result()


# TODO: test CLI command line parsing separately
@istest
def can_deploy_temporarily_using_cli_with_params_passed_on_command_line():
    app_path = testing.example_app_path("just-a-script")
    
    process = _local.spawn([
        "beach", "deploy",
        app_path, "-pport=58080",
    ])
    try:
        response = testing.retry_http_get("http://localhost:58080", timeout=1)
        assert_equal("Hello", response.text)
    finally:
        process.send_signal(signal.SIGINT)
        process.wait_for_result()
    

@istest
def can_register_services_using_cli():
    with tempfile.NamedTemporaryFile() as registry_file:
        config = {"registry": {"path": registry_file.name}}
        
        with tempfile.NamedTemporaryFile() as config_file:
            json.dump(config, config_file)
            config_file.flush()
        
            _local.run([
                "beach", "register",
                "node-0.10", "-ppath=/opt/node-0.10.2/",
                "-c", config_file.name
            ])
            
        registry = beach.registries.FileRegistry(_local, registry_file.name)
        service = registry.find_service("node-0.10")
        assert_equal("/opt/node-0.10.2/", service.provides["path"])
    

@istest
def can_deregister_services_using_cli():
    with tempfile.NamedTemporaryFile() as registry_file:
        registry = beach.registries.FileRegistry(_local, registry_file.name)
        registry.register("node-0.10", provides={})
        
        config = {"registry": {"path": registry_file.name}}
        
        with tempfile.NamedTemporaryFile() as config_file:
            json.dump(config, config_file)
            config_file.flush()
        
            _local.run([
                "beach", "deregister",
                "node-0.10",
                "-c", config_file.name
            ])
            
        assert_equal(None, registry.find_service("node-0.10"))
