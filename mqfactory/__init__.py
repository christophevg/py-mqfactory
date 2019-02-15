__version__ = "0.0.1"

import os
import time
import logging

# setup logging

logger = logging.getLogger()

formatter = logging.Formatter(
  "[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
  "%Y-%m-%d %H:%M:%S %z"
)

if len(logger.handlers) > 0:
  logger.handlers[0].setFormatter(formatter)
else:
  consoleHandler = logging.StreamHandler()
  consoleHandler.setFormatter(formatter)
  logger.addHandler(consoleHandler)

LOG_LEVEL = os.environ.get("LOG_LEVEL") or "DEBUG"
logger.setLevel(logging.getLevelName(LOG_LEVEL))

# provide simple time in milliseconds function

millis = lambda: int(round(time.time() * 1000))

# helper function to apply a list of functions to an object

def wrap(msg, wrappers):
  for wrapper in wrappers:
    wrapper(msg)

# expose MessageQueue class from root, to allow a nice import statement like:
# from mqfactory import MessageQueue
# ;-)
from mqfactory.MessageQueue import Threaded, MessageQueue, DeferException
