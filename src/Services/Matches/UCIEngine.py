import os
import subprocess
import concurrent.futures

from Services.Logging import logger
from Services.Matches.utils import remove_all

SCORE_MATE = 100000

class MoveInfo:
    def __init__(self):
        self.move = None
        self.evaluation = None
        self.depth = None
        self.seldepth = None
        self.nps = None
        self.nodes = None

    def to_dict(self):
        return {
            "move": self.move,
            "eval": self.evaluation,
            "depth": self.depth,
            "seldepth": self.seldepth,
            "nps": self.nps,
            "nodes": self.nodes,
        }

class UCIEngine:
    def __init__(self, executable, log=True):
        self.executable = executable
        self.log = log
        self.process = None

    def __enter__(self):
        self.process = subprocess.Popen([self.executable], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.process is not None:
            self.process.kill()
            self.process = None

    def init(self):
        self._send_message("isready")
        self._send_message("ucinewgame")
        self._send_message("position startpos")

    def set_position(self, move_list):
        self._send_message("position startpos moves {}".format(" ".join(move_list)))

    def get_best_move(self, movetime):
        self._send_message("go movetime {}".format(int(movetime)))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            try:
                future = executor.submit(self._read_best_move)
                move = future.result(timeout=int(movetime * 2))
                return move
            except concurrent.futures.TimeoutError as err:
                return None

    def _send_message(self, message):
        self._assert_process()
        self.process.stdin.write("{}\n".format(message).encode("utf-8"))
        self.process.stdin.flush()

    def _read_best_move(self):
        move_info = None
        while True:
            data = self._read_line()
            if data.startswith("info "):
                parts = self._parse_info(data)
                move_info = MoveInfo()
                move_info.depth = parts["depth"]
                move_info.seldepth = parts["seldepth"]
                move_info.nps = parts["nps"]
                move_info.nodes = parts["nodes"]
                if parts["mate"] is not None:
                    move_info.evaluation = SCORE_MATE - parts["mate"] if parts["mate"] >= 0 else -SCORE_MATE - parts["mate"]
                else:
                    move_info.evaluation = parts["eval"]
            if data.startswith("bestmove "):
                if move_info is None:
                    move_info = MoveInfo()
                move_info.move = self._read_argument(data, "bestmove ", str)
                return move_info

    def _parse_info(self, line):
        return {
            "mate": self._read_argument(line, "score mate ", int),
            "eval": self._read_argument(line, "score cp ", int),
            "depth": self._read_argument(line, "depth ", int),
            "seldepth": self._read_argument(line, "seldepth ", int),
            "nodes": self._read_argument(line, "nodes ", int),
            "nps": self._read_argument(line, "nps ", int),
        }

    def _read_argument(self, line, arg, arg_type=int):
        index = line.find(arg)
        if index < 0:
            return None
        offset = len(arg)
        space = line.find(' ', index + offset + 1)
        if space >= 0:
            return arg_type(line[index + offset : space])
        return arg_type(line[index + offset:])

    def _read_line(self):
        while True:
            data = self.process.stdout.readline()
            if len(data) > 0:
                string = remove_all(data.decode("utf-8"), '\n', '\r')
                if self.log:
                    logger.info(string)
                return string

    def _assert_process(self):
        if self.process is None:
            raise Exception("Process is not valid")
