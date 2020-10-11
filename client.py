import os
import sys
import argparse
import threading
import socket

LOG_TOKEN = "__LOG__"

class ConnectionHandler:
    def __init__(self, server, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server, port))

        thread = threading.Thread(target=self._read_connection, daemon=True)
        thread.start()

    def run_command(self, command):
        self.socket.send(command.encode("utf-8"))

    def _read_connection(self):
        while True:
            data = self.socket.recv(4096)
            if len(data) > 0:
                message = data.decode("utf-8")
                for msg in message.split("\n"):
                    if len(msg) > 0:
                        if msg.startswith(LOG_TOKEN):
                            print(msg[len(LOG_TOKEN):])
                        else:
                            print(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=str, default="localhost", help="Command server address")
    parser.add_argument("--port", type=int, default=9091, help="Command server port")

    args = parser.parse_args()

    connection = ConnectionHandler(args.server, args.port)

    while True:
        command = input("")

        if command == "exit" or command == "quit":
            break

        connection.run_command(command)
