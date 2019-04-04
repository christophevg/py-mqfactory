import time
import logging
import inspect

from threading import Thread

from mqfactory.tools   import wrap
from mqfactory.message import Message
from mqfactory.Queue   import Queue

# a defer exception will skip sending a message and schedule it again at the
# end of the outbox

class DeferException(Exception):
  pass

# the top-level message queue object

class MessageQueue(object):
  def __init__(self, transport, name="mq"):
    self.transport       = transport
    self.name            = name
    self.inbox           = Queue(self.name + "-inbox")
    self.outbox          = Queue(self.name + "-outbox")
    self.before_sending  = []
    self.after_sending   = []
    self.handlers        = {}
    self.before_handling = []
    self.after_handling  = []
    self.transport.connect()

  def send(self, to, payload, tags=None):
    msg = Message(to, payload, tags)
    self.outbox.add(msg)

  def on_message(self, to, handler):
    self.handlers[to] = handler
    def store_to_inbox(message):
      message.private["handler"] = to
      self.inbox.add(message)
    self.transport.on_message(to, store_to_inbox)

  def process_outbox(self):
    self.process(
      self.outbox, self.transport,
      self.before_sending, self.after_sending
    )

  def process_inbox(self):
    self.process(
      self.inbox, self.handlers,
      self.before_handling[::-1], self.after_handling[::-1]
    )

  def send_and_receive(self):
    self.process_outbox()
    self.process_inbox()

  def process(self, box, transport, before, after):
    caller = inspect.getouterframes(inspect.currentframe())[1][3].split("_")[1]
    try:
      message = next(box)
      logging.debug("{0}: processing {1}".format(caller, message))
    except StopIteration:
      return
    try:
      wrap(message, before) # defer here avoids sending
      try:
        transport[message.private["handler"]](message)
      except KeyError:
        transport.send(message)
      wrap(message, after)  # defer here avoids removal
      logging.info("{0}: message sent, removing".format(caller))
      box.remove(message)
    except DeferException:
      box.defer(message)    # defer will put msg at end of queue
    except Exception as e:
      logging.warning("{0}: processing {0} failed".format(caller, str(message)))
      logging.exception("message")
      # TODO: failing messages remain in the queue and might fail forever

def Threaded(mq, interval=0.001):
  def processor():
    while True:
      mq.send_and_receive()
      time.sleep(interval)
  t = Thread(target=processor)
  t.daemon = True
  t.start()
  return mq
