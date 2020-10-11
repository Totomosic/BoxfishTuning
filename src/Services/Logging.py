import os

class Logger:
    def __init__(self):
        pass

    def info(self, *args):
        pass

    def warn(self, *args):
        pass

    def error(self, *args):
        pass

class ConsoleLogger(Logger):
    def __init__(self):
        pass

    def info(self, *args):
        print("[INFO]:", *args)

    def warn(self, *args):
        print("[WARN]:", *args)

    def error(self, *args):
        print("[ERROR]:", *args)

class EventLogger(Logger):
    def __init__(self):
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

        def remove_callback():
            self.callbacks.remove(callback)
        return remove_callback

    def info(self, *args):
        self._write_message("[INFO]:", *args)

    def warn(self, *args):
        self._write_message("[WARN]:", *args)

    def error(self, *args):
        self._write_message("[ERROR]:", *args)

    def _write_message(self, *args):
        message = " ".join([str(a) for a in args])
        for callback in self.callbacks:
            callback(message)

logger = EventLogger()
