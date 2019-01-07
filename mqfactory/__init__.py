__version__ = "0.0.1"

import time

from threading import Thread

class MessageQueue(object):
  def __init__(self, transport):
    self.transport        = transport
    self.outbox           = Outbox()
    self.before_sending   = []
    self.after_receiving  = []

  def send(self, to, payload):
    for wrapper in self.before_sending:
      (to, payload) = wrapper(to, payload)
    self.outbox.append((to, payload))

  def process_outbox(self):
    while len(self.outbox) > 0:
      (to, payload) = self.outbox[0]
      try:
        self.transport.send(to, payload)
        self.outbox.pop(0)
      except Exception as e:
        time.sleep(1)

  def on_message(self, to, handler):
    def wrapped_handler(transport, to, payload):
      for wrapper in self.after_receiving:
        (to, payload) = wrapper(to, payload)
      handler(self, to, payload)
    self.transport.on_message(to, wrapped_handler)


class Outbox(object):
  def __init__(self):
    self.items = []
    self.after_append  = []
    self.after_pop     = []
    self.after_setitem = []

  def append(self, item):
    self.items.append(item)
    for handler in self.after_append:
      handler(self, item)

  def pop(self, index=0):
    item = self.items.pop(index)
    for handler in self.after_pop:
      handler(self, index, item)
    return item

  def __len__(self):
    return len(self.items)

  def __getitem__(self, key):
    return self.items[key]

  def __setitem__(self, key, item):
    self.items[key] = item
    for handler in self.after_setitem:
      handler(self, key, item)


def Threaded(mq, interval=0.1):
  def processor():
    while True:
      mq.process_outbox()
      time.sleep(interval)
  t = Thread(target=processor)
  t.daemon = True
  t.start()
  return mq
