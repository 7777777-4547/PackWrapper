from .PathEnum import PackWrapper

from enum import IntEnum
import logging
import sys

COLORS = {
    'DEBUG': '\033[92m',     # Light Green
    'INFO': '\033[0m',      # Normal(Reset)
    'WARNING': '\033[93m',   # Light Yellow
    'ERROR': '\033[91m',     # Red
    'CRITICAL': '\033[1;30;101m',  # 
    'RESET': '\033[0m'       # Reset
}

class LoggerType(IntEnum):
    
    CRITICAL = logging.CRITICAL
    FATAL = CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    WARN = WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class ColorFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        return f"{COLORS.get(record.levelname, '')}{message} {COLORS['RESET']}"


class Logger:
    
    '''
    Logger class(configured logging),
    if you want to use its right format you need to use the `PackWrapper.config()` function firstly.
    '''
    
    # Logging Format: https://docs.python.org/zh-cn/3/library/logging.html#logrecord-attributes
    
    @staticmethod
    def config(
               filename, filemode, encoding = "utf-8",
               level = logging.DEBUG,
               format = "[%(asctime)s][%(threadName)s/%(levelname)s]: %(message)s", 
               datefmt = "%Y/%m/%d|%H:%M:%S"
               ):
                
        filename = PackWrapper.ROOT / filename

        logger = logging.getLogger()
        logger.setLevel(level)

        file_handler = logging.FileHandler(filename, filemode, encoding)
        file_handler.setFormatter(logging.Formatter(format, datefmt))

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter(format, datefmt))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
            
    
    @staticmethod
    def _exception(msg, *args, exc_info=True, **kwargs):
        
        '''
        Log a message with severity 'ERROR' on the root logger, with exception
        information. If the logger has no handlers, basicConfig() is called to add
        a console handler with a pre-defined format.
        
        The difference: Include `raise` to faster end the progarm if the program have the error.
        '''
        
        logging.exception(msg, *args, exc_info=exc_info, **kwargs)
        
        if exc_info and isinstance(exc_info, BaseException):
            raise exc_info from None
        elif sys.exc_info()[0] is not None:
            raise
    
    
    @staticmethod
    def _warning(msg, *args, exc_info=True, **kwargs):
        
        '''
        Log a message with severity 'WARNING' on the root logger. If the logger has
        no handlers, call basicConfig() to add a console handler with a pre-defined
        format.
        
        The difference: Exception infomation will be logged.
        '''

        logging.warning(msg, *args, exc_info=exc_info, **kwargs)
        
   
    critical = logging.critical
    fatal = logging.fatal
    error = logging.error
    exception = _exception
    warning = _warning
    warn = logging.warn
    info = logging.info
    debug = logging.debug
        