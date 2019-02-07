import time

from mqfactory               import MessageQueue, millis
from mqfactory.transport.qos import check_timeout, Acknowledgement, Acknowledging

def test_check_timeout(message):
  message.tags["sent"] = millis()
  assert not check_timeout(message)
  message.tags["sent"] = millis() - 5000
  assert check_timeout(message)

def test_request_ack():
  # TODO
  pass