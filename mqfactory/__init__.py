__version__ = "0.0.1"

import time
import logging

from threading import Thread

from mqfactory.Outbox import Outbox
from mqfactory.message import Message

millis = lambda: int(round(time.time() * 1000))

class DeferException(Exception):
  pass

def wrap(msg, wrappers):
  for wrapper in wrappers:
    wrapper(msg)

class MessageQueue(object):
  def __init__(self, transport):
    self.transport        = transport
    self.outbox           = Outbox(self)
    self.before_sending   = []
    self.after_sending    = []
    self.before_handling  = []
    self.after_handling   = []
    self.transport.connect()

  def send(self, to, payload, tags=None):
    msg = Message(to, payload, tags)
    self.outbox.append(msg)

  def process_entire_outbox(self):
    try:
      while True:
        self.process_outbox()
    except StopIteration:
      pass

  def process_outbox(self):
    msg = next(self.outbox)
    try:
      wrap(msg, self.before_sending)
      self.transport.send(msg)
      wrap(msg, self.after_sending)
      self.outbox.pop()
    except DeferException:
      self.outbox.defer()
    except Exception as e:
      logging.warn("sending failed: {0}".format(str(e)))
      logging.exception("message")
    time.sleep(0.1)

  def on_message(self, to, handler):
    def wrapped_handler(msg):
      try:
        wrap(msg, self.before_handling[::-1])
        handler(msg)
        wrap(msg, self.after_handling[::-1])
      except Exception as e:
        logging.error(str(e))
    self.transport.on_message(to, wrapped_handler)

def Threaded(mq, interval=0.1):
  def processor():
    while True:
      mq.process_entire_outbox()
      time.sleep(interval)
  t = Thread(target=processor)
  t.daemon = True
  t.start()
  return mq
