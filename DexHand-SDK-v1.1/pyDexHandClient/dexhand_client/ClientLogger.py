import datetime
import logging
import colorlog
import os


class ClientLogger:

    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def __init__(self, console_log_level=logging.INFO, ignore_myself=False):
        self.logger = logging.getLogger("DexHandLogger")
        self.logger.setLevel(logging.DEBUG)
        self.ignore_myself = ignore_myself

        log_dir = "DexHandLogs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.create_time = datetime.datetime.now().strftime("%Y%m%d")
        self.file_logger = logging.FileHandler(log_dir + "/" + f"{self.create_time}.log")
        self.file_logger.setLevel(logging.DEBUG)

        self.console_logger = logging.StreamHandler()
        self.console_logger.setLevel(console_log_level)
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)s] %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
        self.console_logger.setFormatter(formatter)
        formatter = logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
        self.file_logger.setFormatter(formatter)

        self.logger.addHandler(self.console_logger)
        self.logger.addHandler(self.file_logger)

    def unpack_msg(self, data):
        if data["Device"] == "Hand":
            self.push_log(data["LogLevel"], "Hand: " + data["Msg"], from_server=True)
        elif data["Device"] == "Tac3D":
            self.push_log(data["LogLevel"], "Tac3D: " + data["Msg"], from_server=True)
        elif data["Device"] == "Server":
            self.push_log(data["LogLevel"], "Server: " + data["Msg"], from_server=True)
        else:
            self.push_log(logging.ERROR, "a msg from unknown device was received.", from_server=True)

    def push_log(self, level, msg, from_server=False):
        if not from_server and self.ignore_myself and level == logging.INFO:
            level = logging.DEBUG
        if level == logging.DEBUG:
            self.logger.debug(msg)
        elif level == logging.INFO:
            self.logger.info(msg)
        elif level == logging.WARNING:
            self.logger.warning(msg)
        elif level == logging.ERROR:
            self.logger.error(msg)
        elif level == logging.FATAL:
            self.logger.critical(msg)
        elif level == logging.NOTSET:
            pass
        else:
            self.logger.error("a msg with invalid logger level was received.")
