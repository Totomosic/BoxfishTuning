import os
import json

from Services.Logging import logger

METADATA_JSON_FILE = "Meta.json"

class ExecutableData:
    def __init__(self):
        self.filepath = None
        self.filename = None
        self.name = None

# Class responsible for managing the engine executables
class CacheManager:
    def __init__(self, cache_directory):
        self.directory = cache_directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory, exist_ok=True)

        self.metadata = {}
        self.metadata_filename = os.path.join(self.directory, METADATA_JSON_FILE)
        if not os.path.exists(self.metadata_filename):
            logger.warn("Executable {} does not exist".format(METADATA_JSON_FILE))
            with open(self.metadata_filename, "w") as f:
                json.dump({}, f)
        self.metadata = self._reload_metadata()

        executables = self.get_executables()
        logger.info("Cache starting... Found {} executables: ".format(len(executables)))
        for exe in executables:
            logger.info(exe.name)

    def reload(self):
        self.metadata = self._reload_metadata()

    def add_executable(self, name, filename):
        full_path = os.path.join(self.directory, os.path.basename(filename))
        os.rename(filename, full_path)

        self.metadata[os.path.relpath(full_path, self.directory)] = { "name": name }
        self._write_metadata()

    def remove_executable(self, name):
        for key in self.metadata:
            if self.metadata[key] == name:
                name = key
        if not os.path.isabs(name):
            name = os.path.join(self.directory, name)
        if os.path.exists(name):
            os.remove(name)

        filename = os.path.relpath(name, self.directory)
        if filename in self.metadata:
            del self.metadata[filename]
            self._write_metadata()

    def get_executables(self):
        results = []
        for filename in os.listdir(self.directory):
            full_path = os.path.join(self.directory, filename)
            if os.path.isfile(full_path) and filename != METADATA_JSON_FILE:
                data = ExecutableData()
                data.filename = filename
                data.filepath = full_path
                if filename in self.metadata:
                    for key in self.metadata[filename]:
                        setattr(data, key, self.metadata[filename][key])
                results.append(data)
        return results

    def _reload_metadata(self):
        with open(self.metadata_filename, "r") as f:
            data = json.load(f)
        for executable in self.get_executables():
            if executable.filename not in data:
                logger.warn("Found executable {} without entry in {}".format(executable.filename, METADATA_JSON_FILE))
        return data

    def _write_metadata(self):
        with open(self.metadata_filename, "w") as f:
            json.dump(self.metadata, f)
