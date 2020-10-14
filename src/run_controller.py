import os
import sys
import argparse
import socket
import threading
import re
import json
import traceback

from Services.Logging import logger

from Services.Cache.CacheManager import CacheManager

from Services.Matches.BoxfishSource import BoxfishSource, checkout_source
from Services.Matches.MatchManager import MatchManager
from Services.Matches.utils import ensure_directory_exists, read_config_file, delete_recursive

OS_LINUX = "linux"
OS_WINDOWS = "windows"

class Config:
    def __init__(self):
        self.server = None
        self.port = None
        self.os = None
        
        self.cache_directory = "Engines/"

        self.boxfish_repo = "https://github.com/Totomosic/Boxfish"
        self.boxfish_directory = None

        self.match_directory = "Matches/"

class CommandServer:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.callback = None

        self.socket.bind((self.server, self.port))

    def set_command_listener(self, callback):
        self.callback = callback

    def start(self, backlog=5):
        self.socket.listen(backlog)

        logger.info("Starting command server listening at {} port {}".format(self.server, self.port))

        self._accept_connections()

    def _accept_connections(self):
        while True:
            socket, address = self.socket.accept()
            logger.info("Got connection from {}".format(address[0]))
            thread = threading.Thread(target=self._read_connection, args=(socket, address))
            thread.start()

    def _read_connection(self, socket, address):
        def send_logging(message):
            try:
                socket.send(("__LOG__" + message + '\n').encode("utf-8"))
            except Exception:
                pass

        remove_callback = logger.add_callback(send_logging)
        while True:
            try:
                data = socket.recv(4096)
                if len(data) > 0:
                    command = data.decode("utf-8")
                    if self.callback:
                        result = self.callback(command)
                    else:
                        result = "No command handler"
                    if len(result) == 0:
                        result = "Ok"
                    socket.send(result.encode("utf-8"))
                else:
                    break
            except Exception as e:
                try:
                    socket.send(traceback.format_exc().encode("utf-8"))
                except Exception:
                    pass
                break
        logger.info("Connection disconnected {}".format(address[0]))
        remove_callback()

class Controller:
    def __init__(self, config):
        self.config = config

        self.cache_manager = CacheManager(self.config.cache_directory)

        self.commands = {}
        self.commands["help"] = self._handle_help
        self.commands["list_engines"] = self._handle_list_engines
        self.commands["list_matches"] = self._handle_list_matches
        self.commands["clear_matches"] = self._handle_clear_matches
        self.commands["summarise"] = self._handle_summarise
        self.commands["play"] = self._handle_play

        self.command_server = CommandServer(self.config.server, int(self.config.port))
        self.command_server.set_command_listener(self.process_commandline)
        self.command_server.start()

    def process_commandline(self, command):
        parts = re.findall(r'(?:[^\s "]|"(?:\\.|[^"])*")+', command)
        if len(parts) > 0:
            command_name = parts[0]
            if command_name in self.commands:
                return self.commands[command_name](parts[1:])
            else:
                return "Unknown command: {}".format(command_name)
        else:
            return "Invalid command: {}".format(command)

    def _handle_help(self, args):
        return '\n'.join([key for key in self.commands])

    def _handle_list_engines(self, args):
        return '\n'.join(map(lambda data: data.name, self.cache_manager.get_executables()))

    def _handle_list_matches(self, args):
        return '\n'.join(os.listdir(self.config.match_directory))

    def _handle_clear_matches(self, args):
        delete_recursive(self.config.match_directory)
        ensure_directory_exists(self.config.match_directory)
        return "Ok"

    def _handle_summarise(self, arg_list):
        parser = argparse.ArgumentParser()
        parser.add_argument("--match", type=str, required=True, help="Match result file to summarise")

        try:
            args = parser.parse_args(arg_list)

            summary = ""
            match_file = os.path.join(self.config.match_directory, args.match)
            with open(match_file, "r") as f:
                data = json.load(f)
            summary += "Time to Move: {}ms\n".format(data["movetime"])
            winner = data["result"]
            if winner == 1:
                summary += "Result: White won by {}".format(data["description"])
            elif winner == -1:
                summary += "Result: Black won by {}".format(data["description"])
            else:
                summary += "Result: Draw - {}".format(data["description"])
            summary += "\nMove Count: {}".format(len(data["moves"]))
            return summary

        except SystemExit:
            return parser.format_help()

    def _handle_play(self, arg_list):
        parser = argparse.ArgumentParser()
        parser.add_argument("--commit", type=str, default=None, help="Which Boxfish commit to use")
        parser.add_argument("--branch", type=str, default=None, help="Which Boxfish branch to use")
        parser.add_argument("--ttm", type=int, action="append", help="Times to move in millseconds of each match")

        try:
            args = parser.parse_args(arg_list)

            if args.commit:
                checkout_source(self.config.boxfish_directory, self.config.boxfish_repo, commit=args.commit)
            elif args.branch:
                checkout_source(self.config.boxfish_directory, self.config.boxfish_repo, branch=args.branch)
            else:
                checkout_source(self.config.boxfish_directory, self.config.boxfish_repo)

            boxfish_source = BoxfishSource(self.config.boxfish_directory)
            if self.config.os == OS_LINUX:
                boxfish_exe = boxfish_source.build_linux()
            else:
                boxfish_exe = boxfish_source.build_windows("C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\MSBuild\\Current\\Bin\\MSBuild.exe")

            ensure_directory_exists(self.config.match_directory)

            for executable_data in self.cache_manager.get_executables():
                for time in args.ttm:
                    manager = MatchManager(boxfish_exe, executable_data.filepath)
                    match_result = manager.play_match(time)
                    if match_result[0]:
                        with open(os.path.join(self.config.match_directory, "Boxfish-{}-{}.json".format(executable_data.name, time)), "w") as f:
                            json.dump(match_result[0], f)
                    if match_result[1]:
                        with open(os.path.join(self.config.match_directory, "{}-Boxfish-{}.json".format(executable_data.name, time)), "w") as f:
                            json.dump(match_result[1], f)
            return "Done."

        except SystemExit:
            return parser.format_help()

def read_config(config_file):
    config_dict = read_config_file(config_file)
    config = Config()
    for key in config_dict:
        setattr(config, key, config_dict[key])
    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", type=str, default="Controller.cfg", help="Config file name")

    args = parser.parse_args()

    controller = Controller(read_config(args.config_file))
