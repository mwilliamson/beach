import tempfile
import signal
import json

import spur
from nose.tools import istest, assert_equal

from . import testing

_local = spur.LocalShell()


@istest
def can_deploy_temporarily_using_cli():
    app_path = testing.example_app_path("just-a-script")
    # TODO: allow integer parameters
    params = {"port": "58080"}
    config = {"params": params}
    
    with tempfile.NamedTemporaryFile() as config_file:
        config_file.write(json.dumps(config))
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
    
    
