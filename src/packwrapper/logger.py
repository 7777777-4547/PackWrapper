from functools import wraps, partial
from pathlib import Path
from typing import Any, TypeVar, ParamSpec, NoReturn, Callable
from enum import IntEnum
import threading
import logging
import sys
import warnings

P = ParamSpec("P")
R = TypeVar("R")


COLORS = {
    "DEBUG": "\033[92m",  # Light Green
    "INFO": "\033[0m",  # Normal(Reset)
    "WARNING": "\033[93m",  # Light Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[1;30;101m",  # Light Red(Background)
    "RESET": "\033[0m",  # Reset
}


class LoggerType(IntEnum):
    CRITICAL = logging.CRITICAL
    FATAL = CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class Logger:
    """
    Logger class(configured logging),
    if you want to use its right format you need to use the `PackWrapper.config()` function firstly.
    """

    ROOT = Path("./.packwrapper/log")

    class ID:
        _local = threading.local()

        @classmethod
        def set(cls, id: str | None):
            cls._local._id = id

        @classmethod
        def get(cls):
            return getattr(cls._local, "_id", None)

        @classmethod
        def reset(cls):
            if hasattr(cls._local, "_id"):
                delattr(cls._local, "_id")

        def __init__(self, _id: str | None = None):
            self.__id = _id

        def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs):
                self.set(self.__id)
                result = func(*args, **kwargs)
                self.reset()
                return result

            return wrapper

    class ExtID(ID):
        @classmethod
        def set(cls, id: str | None):

            if super().get() is None:
                super().set(f"{id}")
            else:
                cls._local._id = id
                super().set(f"{super().get()} | {id}")

        @classmethod
        def get(cls):
            return getattr(cls._local, "_id", None)

        @classmethod
        def reset(cls):
            current_id = super().get()
            if current_id is not None:
                parts = f"{current_id}".split(" | ")
                if len(parts) > 1:
                        super().set(" | ".join(parts[:-1]))
                else:
                    super().reset()

        def __init__(self, _id: str | None = None):
            self.__id = _id

        def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs):
                self.set(self.__id)
                result = func(*args, **kwargs)
                self.reset()
                return result

            return wrapper

    class CustomFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord):

            if Logger.ID.get() is None:
                record.id = ""
            else:
                record.id = f"[{Logger.ID.get()}] "

            return super().format(record)

    class CustomFormatterColored(CustomFormatter):
        def format(self, record: logging.LogRecord):
            message = super().format(record)
            return f"{COLORS.get(record.levelname, '')}{message}{COLORS['RESET']}"

    # Logging Format: https://docs.python.org/zh-cn/3/library/logging.html#logrecord-attributes

    @staticmethod
    def config(
        filename,
        filemode,
        encoding="utf-8",
        level=LoggerType.DEBUG,
        format="[%(asctime)s][%(threadName)s/%(levelname)s]: %(id)s%(message)s",
        datefmt="%Y/%m/%d|%H:%M:%S",
        multi_thread=False,
    ):

        filename = Logger.ROOT / filename

        logger = logging.getLogger()
        logger.setLevel(level)

        file_handler = logging.FileHandler(filename, filemode, encoding)
        file_handler.setFormatter(Logger.CustomFormatter(format, datefmt))

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(Logger.CustomFormatterColored(format, datefmt))

        if multi_thread:
            console_handler.setLevel(LoggerType.WARNING)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        warnings.showwarning = Logger._showwarning

    @staticmethod
    def get_current_level():
        return logging.getLogger().level

    @staticmethod
    def error(
        msg, *args, exc_info: Any = None, stack_info: bool = True, **kwargs
    ) -> NoReturn:
        """
        Log a message with severity 'ERROR' on the root logger, with exception
        information. If the logger has no handlers, basicConfig() is called to add
        a console handler with a pre-defined format.

        The difference: Include `raise` to faster end the progarm.
        """

        logging.error(msg, *args, exc_info=exc_info, stack_info=stack_info, **kwargs)

        if exc_info and isinstance(exc_info, BaseException):
            raise exc_info from None
        else:
            if sys.exc_info()[0] is not None:
                raise
            else:
                raise RuntimeError(f"Logged error: {msg}")

    @staticmethod
    def exception(
        msg, *args, exc_info: Any = None, stack_info: bool = True, **kwargs
    ) -> NoReturn:
        """
        Log a message with severity 'ERROR' on the root logger, with exception
        information. If the logger has no handlers, basicConfig() is called to add
        a console handler with a pre-defined format.

        The difference: Include `raise` to faster end the progarm.
        """

        logging.exception(
            msg, *args, exc_info=exc_info, stack_info=stack_info, **kwargs
        )

        if exc_info and isinstance(exc_info, BaseException):
            raise exc_info from None
        else:
            if sys.exc_info()[0] is not None:
                raise
            else:
                raise RuntimeError(f"Logged exception: {msg}")

    @staticmethod
    def warning(msg, *args, exc_info: Any = None, stack_info: bool = True, **kwargs):
        """
        Log a message with severity 'WARNING' on the root logger. If the logger has
        no handlers, call basicConfig() to add a console handler with a pre-defined
        format.

        The difference: Exception infomation will be logged.
        """

        logging.warning(msg, *args, exc_info=exc_info, stack_info=stack_info, **kwargs)

    @staticmethod
    def _showwarning(message, category, filename, lineno, file=None, line=None):
        msg_ = f"{category.__name__}: {message}"
        logging.warning(msg_, stack_info=True, stacklevel=4)

    critical = logging.critical
    fatal = logging.fatal
    info = logging.info
    debug = logging.debug

    @staticmethod
    def log(*msg, type_: LoggerType):
        _log: Callable[..., NoReturn | None] | None = None
        match type_:
            case LoggerType.CRITICAL:
                _log = Logger.critical
            case LoggerType.FATAL:
                _log = Logger.fatal
            case LoggerType.ERROR:
                _log = Logger.error
            case LoggerType.WARNING:
                _log = Logger.warning
            case LoggerType.INFO:
                _log = Logger.info
            case LoggerType.DEBUG:
                _log = Logger.debug
            case LoggerType.NOTSET:
                _log = partial(logging.log, level=LoggerType.NOTSET)
            case _:
                raise Exception(f"Unknown log type: {type_}")

        for _msg in msg:
            _log(_msg)
