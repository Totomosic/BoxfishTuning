import sys
import os
import subprocess
import shutil

def directory_exists(directory):
    return os.path.exists(directory)

def ensure_directory_exists(directory):
    os.makedirs(directory, exist_ok=True)

def delete_recursive(directory):
    try:
        shutil.rmtree(directory)
    except Exception as e:
        print(e)

def read_config_file(filename):
    config = {}
    with open(filename, "r") as f:
        for line in f.readlines():
            if '=' in line:
                parts = line.split('=')
                if len(parts) == 2:
                    config[parts[0].lstrip().rstrip()] = parts[1].lstrip().rstrip()
    return config
    
def remove_all(string, *chars):
    for c in chars:
        string = string.replace(c, '')
    return string

class ChangeDirectory:
    def __init__(self, dest):
        self.destination = dest
        self.current = None

    def __enter__(self):
        if self.destination is not None:
            self.current = os.getcwd()
            os.chdir(self.destination)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.destination is not None:
            os.chdir(self.current)
            self.current = None

class CommandLine:
    SUCCESS = 0

    def __init__(self, command_line, working_directory=None):
        self.command = command_line
        self.working_directory = working_directory

    def run(self):
        with ChangeDirectory(self.working_directory):
            print(self.command)
            return subprocess.run(self.command).returncode

    @staticmethod
    def chain(*command_lines, working_directory=None):
        for cmd_line in command_lines:
            if CommandLine(cmd_line, working_directory=working_directory).run() != CommandLine.SUCCESS:
                return False
        return True
