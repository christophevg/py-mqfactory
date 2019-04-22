__version__ = "0.0.4"

# expose main MQ classes from the module root, to allow a nice import statement
# like: from mqfactory import MessageQueue ;-)

from mqfactory.message      import Message
from mqfactory.Queue        import Queue
from mqfactory.MessageQueue import Threaded, MessageQueue, DeferException
