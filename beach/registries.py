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
        registry_json = self._read_registry()
        registry_json[name] = {"provides": provides}
        with self._shell.open(self._path, "w") as registry_file:
            json.dump(registry_json, registry_file)
    
    def find_service(self, name):
        service_json = self._read_registry().get(name)
        if service_json is None:
            return None
        else:
            return _read_service(service_json)
    
    def _read_registry(self):
        with self._shell.open(self._path, "r") as registry_file:
            try:
                return json.load(registry_file)
            except ValueError:
                registry_file.seek(0)
                if self._is_empty_file(registry_file):
                    return {}
                else:
                    raise ValueError("Registry file was not valid JSON")
    
    def _is_empty_file(self, fileobj):
        return fileobj.read().strip() == ""


def _read_service(service_json):
    return Service(provides=service_json["provides"])


class Service(object):
    def __init__(self, provides):
        self.provides = provides
