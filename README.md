# Beach

A tool for deploying applications.
Meant for fun rather than production use.

# Tests

Run `make tests` to run the tests.

Slow tests are marked using the `slow` attribute,
meaning the remaining tests can be run like so:

```sh
_virtualenv/bin/nosetests tests --attr '!slow'
```

This will still test the core logic,
but not interaction with some pieces that are critical with production use
such as interaction with runit or uploading over SSH.
