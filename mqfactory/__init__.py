__version__ = "0.0.1"

import time
import logging

from threading import Thread

from mqfactory.Outbox import Outbox
from mqfactory.message import Message

millis = lambda: int(round(time.time() * 1000))

class DeferException(Exception):
  pass

class MessageQueue(object):
  def __init__(self, transport):
    self.transport        = transport
    self.outbox           = Outbox(self)
    self.before_sending   = []
    self.after_sending    = []
    self.after_receiving  = []
    self.after_handling   = []
    self.transport.connect()

  def send(self, to, payload):
    msg = Message(to, payload)
    self.outbox.append(msg)

  def process_outbox(self):
    while len(self.outbox) > 0:
      msg = self.outbox[0]
      try:
        for wrapper in self.before_sending:
          wrapper(msg)
        self.transport.send(msg)
        self.outbox.pop(0)
        for wrapper in self.after_sending:
          wrapper(msg)
      except DeferException:
        self.outbox.defer(0)
      except Exception as e:
        logging.warn("sending failed: {0}".format(str(e)))
        time.sleep(1)

  def on_message(self, to, handler):
    def wrapped_handler(msg):
      for wrapper in self.after_receiving[::-1]:
        wrapper(msg)
      handler(msg)
      for wrapper in self.after_handling[::-1]:
        wrapper(msg)
    self.transport.on_message(to, wrapped_handler)


def Threaded(mq, interval=0.1):
  def processor():
    while True:
      mq.process_outbox()
      time.sleep(interval)
  t = Thread(target=processor)
  t.daemon = True
  t.start()
  return mq
