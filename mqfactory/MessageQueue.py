import time
import logging

from threading import Thread

from mqfactory.message import Message
from mqfactory.Outbox import Outbox

# a defer exception will skip sending a message and schedule it again at the
# end of the outbox

class DeferException(Exception):
  pass

# helper function to apply a list of functions to an object

def wrap(msg, wrappers):
  for wrapper in wrappers:
    wrapper(msg)

# the top-level message queue object

def NoneGenerator():
  return None

class MessageQueue(object):
  def __init__(self, transport, id_generator=NoneGenerator, clock=None):
    self.transport        = transport
    self.id_generator     = id_generator
    self.outbox           = Outbox(self, clock=clock)
    self.before_sending   = []
    self.after_sending    = []
    self.before_handling  = []
    self.after_handling   = []
    self.transport.connect()

  def send(self, to, payload, tags=None):
    msg = Message(to, payload, tags, id=self.id_generator())
    self.outbox.add(msg)

  def process_entire_outbox(self):
    try:
      while True:
        self.process_outbox()
    except StopIteration:
      pass

  def process_outbox(self):
    message = next(self.outbox)
    try:
      wrap(message, self.before_sending) # defer here avoids sending
      self.transport.send(message)
      wrap(message, self.after_sending)  # defer here avoids deletion
      self.outbox.remove(message)
    except DeferException:
      self.outbox.defer(message)         # defer will put msg at end of queue
    except Exception as e:
      logging.warning("sending of {0} failed: {1}".format(str(message), str(e)))
      logging.exception("message")

  def on_message(self, to, handler):
    def wrapped_handler(message):
      try:
        wrap(message, self.before_handling[::-1])
        handler(message)
        wrap(message, self.after_handling[::-1])
      except Exception as e:
        logging.error(str(e))
    self.transport.on_message(to, wrapped_handler)

def Threaded(mq, interval=0.001):
  def processor():
    while True:
      mq.process_entire_outbox()
      time.sleep(interval)
  t = Thread(target=processor)
  t.daemon = True
  t.start()
  return mq
