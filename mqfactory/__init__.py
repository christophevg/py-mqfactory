__version__ = "0.0.3"

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
  logger.handlers[0].setFormatter(formatter) # pragma: no cover
else:
  consoleHandler = logging.StreamHandler()
  consoleHandler.setFormatter(formatter)
  logger.addHandler(consoleHandler)

LOG_LEVEL = os.environ.get("LOG_LEVEL") or "WARN"
logger.setLevel(logging.getLevelName(LOG_LEVEL))

# expose MessageQueue class from root, to allow a nice import statement like:
# from mqfactory import MessageQueue
# ;-)
from mqfactory.MessageQueue import Threaded, MessageQueue, DeferException
from mqfactory.Queue        import Queue
