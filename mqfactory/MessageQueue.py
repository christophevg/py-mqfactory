import time

from threading import Thread

from mqfactory.Outbox import Outbox

class MessageQueue(object):
  def __init__(self, transport):
    self.transport        = transport
    self.outbox           = Outbox(self)
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


def Threaded(mq, interval=0.1):
  def processor():
    while True:
      mq.process_outbox()
      time.sleep(interval)
  t = Thread(target=processor)
  t.daemon = True
  t.start()
  return mq
