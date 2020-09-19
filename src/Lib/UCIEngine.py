import os
import subprocess
import concurrent.futures

from Lib.utils import remove_all

SCORE_MATE = 100000

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
                move, evaluation = future.result(timeout=int(movetime * 2))
                return move, evaluation
            except concurrent.futures.TimeoutError as err:
                return None, None

    def _send_message(self, message):
        self._assert_process()
        self.process.stdin.write("{}\n".format(message).encode("utf-8"))
        self.process.stdin.flush()

    def _read_best_move(self):
        current_evaluation = None
        while True:
            data = self._read_line()
            if data.startswith("info "):
                index = data.find(" score ")
                if index >= 0:
                    offset = len("mate ")
                    is_mate = True
                    prev_index = index
                    index = data.find("mate ", index)
                    if index < 0:
                        index = data.find("cp ", prev_index)
                        offset = len("cp ")
                        is_mate = False
                    space = data.find(" ", index + offset + 1)
                    value = int(data[index + offset : space])
                    current_evaluation = value if not is_mate else (SCORE_MATE - value if value >= 0 else -SCORE_MATE + value)
            if data.startswith("bestmove "):
                return data[len("bestmove "):], current_evaluation

    def _read_line(self):
        while True:
            data = self.process.stdout.readline()
            if len(data) > 0:
                string = remove_all(data.decode("utf-8"), '\n', '\r')
                if self.log:
                    print(string)
                return string

    def _assert_process(self):
        if self.process is None:
            raise Exception("Process is not valid")
