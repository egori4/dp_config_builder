import sys
import os
from datetime import datetime

class Logger:
    VERBOSITY_LEVELS = {"disabled": 0, "info": 1, "debug": 2}

    def __init__(self, verbosity="disabled", log_to_file=True):
        self.verbosity = verbosity.lower()
        self.log_to_file = log_to_file

        if self.log_to_file:
            self.log_dir = "log"
            os.makedirs(self.log_dir, exist_ok=True)
            # Use only date for log file name, so one file per run/day
            date_str = datetime.now().strftime("%Y%m%d")
            self.log_file_path = os.path.join(self.log_dir, f"log_{date_str}.log")
            self.log_file = open(self.log_file_path, "a", encoding="utf-8")

    def set_verbosity(self, level):
        self.verbosity = level.lower()

    def _should_log(self, level):
        return self.VERBOSITY_LEVELS.get(self.verbosity, 0) >= self.VERBOSITY_LEVELS.get(level, 0)

    def _format_message(self, message, level, indent):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        indent_str = "  " * indent
        return f"{indent_str}[{timestamp}] [{level.upper()}] {message}"

    def _print(self, message, level, indent):
        if self._should_log(level):
            formatted = self._format_message(message, level, indent)
            print(formatted)
            sys.stdout.flush()
            if self.log_to_file:
                self._write_to_file(formatted)

    def _write_to_file(self, message):
        try:
            self.log_file.write(message + "\n")
            self.log_file.flush()
        except Exception as e:
            print(f"[LOGGER ERROR] Failed to write to log file: {e}")

    def info(self, message, indent=0):
        self._print(message, "info", indent)

    def warning(self, message, indent=0):
        formatted = self._format_message(message, "warning", indent)
        print(formatted)
        sys.stdout.flush()
        if self.log_to_file:
            self._write_to_file(formatted)

    def debug(self, message, indent=0):
        self._print(message, "debug", indent)

    def error(self, message, indent=0):
        formatted = self._format_message(message, "error", indent)
        print(formatted)
        sys.stdout.flush()
        if self.log_to_file:
            self._write_to_file(formatted)

    def close(self):
        if self.log_to_file and hasattr(self, 'log_file'):
            self.log_file.close()
