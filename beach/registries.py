import json


class InMemoryRegistry(object):
    def __init__(self):
        self._services = {}
    
    def register(self, name, provides):
        self._services[name] = Service(provides)
    
    def find_service(self, name):
        return self._services.get(name)


class FileRegistry(object):
    def __init__(self, shell, path):
        self._shell = shell
        self._path = path
    
    def register(self, name, provides):
        # TODO: don't overwrite existing services
        with self._shell.open(self._path, "w") as registry_file:
            json.dump({name: {"provides": provides}}, registry_file)
    
    def find_service(self, name):
        with self._shell.open(self._path) as registry_file:
            registry_json = json.load(registry_file)
            return _read_service(registry_json[name])


def _read_service(service_json):
    return Service(provides=service_json["provides"])


class Service(object):
    def __init__(self, provides):
        self.provides = provides
