import logging
import queue
import multiprocessing as mp
from logging.handlers import QueueHandler, QueueListener
from datetime import datetime

def launch_logger_listener(filepath, controller=False):
    # Get queue
    q = mp.Queue(-1)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)-8s: %(message)s')

    # create file handler which logs even debug messages
    fh = logging.FileHandler(filepath)
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.INFO)
    
    # Start queue listener using the stream handler above
    ql = QueueListener(q, fh, ch, respect_handler_level=True)
    ql.start()
    
    return q, ql

def create_logger(q, controller=False):
    loggerName = 'controller' if controller else 'simulation'
    # Create log and set handler to queue handle
    log = logging.getLogger(loggerName)
    log.setLevel(logging.DEBUG) # Log level = DEBUG
    qh = QueueHandler(q)
    log.addHandler(qh)

    log.info('Initialized the logger')

    return log