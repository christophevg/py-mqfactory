import time
import logging

from threading import Thread

from mqfactory         import wrap
from mqfactory.message import Message
from mqfactory.Queue   import Queue

# a defer exception will skip sending a message and schedule it again at the
# end of the outbox

class DeferException(Exception):
  pass

# the top-level message queue object

def NoneGenerator():
  return None

class MessageQueue(object):
  def __init__(self, transport, ids=NoneGenerator, ticks=None):
    self.transport       = transport
    self.ids             = ids
    self.inbox           = Queue(self, ticks=ticks)
    self.outbox          = Queue(self, ticks=ticks)
    self.before_sending  = []
    self.after_sending   = []
    self.handlers        = {}
    self.before_handling = []
    self.after_handling  = []
    self.transport.connect()

  def send(self, to, payload, tags=None):
    msg = Message(to, payload, tags, id=self.ids())
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
    try:
      message = next(box)
    except StopIteration:
      return
    try:
      wrap(message, before) # defer here avoids sending
      try:
        transport[message.private["handler"]](message)
      except KeyError:
        transport.send(message)
      wrap(message, after)  # defer here avoids removal
      box.remove(message)
    except DeferException:
      box.defer(message)    # defer will put msg at end of queue
    except Exception as e:
      logging.warning("processing {0} failed: {1}".format(str(message), str(e)))
      logging.exception("message")

def Threaded(mq, interval=0.001):
  def processor():
    while True:
      mq.send_and_receive()
      time.sleep(interval)
  t = Thread(target=processor)
  t.daemon = True
  t.start()
  return mq
