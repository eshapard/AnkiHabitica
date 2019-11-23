# Class for storing and sharing common data such as
#	config and settings data
from . import logging
from .logging import handlers
import os


class AnkiHabiticaCommon:
    config = {}  # dictionary for configuration
    user_settings = {}
    log = logging.Logger

    @classmethod
    def setupLog(cls):
        cls.log = logging.getLogger('AnkiHabitica')
        if cls.user_settings["debug"]:
            cls.log.setLevel(logging.DEBUG)
        else:
            cls.log.setLevel(logging.ERROR)

        logName = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "AnkiHabitica.log")

        roll = os.path.isfile(logName)
        fh = logging.handlers.RotatingFileHandler(logName, backupCount=5)
        if roll:  # log already exists, roll over!
                fh.doRollover()

        fmt = logging.Formatter(
            '%(asctime)s [%(threadName)14s:%(filename)18s:%(lineno)5s - %(funcName)30s()] %(levelname)8s: %(message)s')
        fh.setFormatter(fmt)
        cls.log.addHandler(fh)

    class settings:
        pass  # empty class for holding settings
