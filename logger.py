import logging
import sys


def set_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    return logger
