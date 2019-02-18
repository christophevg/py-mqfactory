import time
import logging

from mqfactory               import MessageQueue, millis
from mqfactory.message       import Message
from mqfactory.transport.qos import check_timeout, Acknowledgement, Acknowledging

def test_check_timeout(message):
  message.tags["sent"] = millis()
  assert not check_timeout(message)
  message.tags["sent"] = millis() - 5000
  assert check_timeout(message)

def mocked_to(answers=[]):
  def f(msg):
    try:
      return answers.pop(0)
    except IndexError:
      return False
  return f

def setup_mq(transport, tos=[], ack_channel="testing", ids=None):
  if not ids is None:
    mq = MessageQueue(transport, ids=ids)
  else:
    mq = MessageQueue(transport)
  ack = Acknowledgement(mq, timedout=mocked_to(tos), ack_channel=ack_channel)
  return Acknowledging(mq, ack=ack)

def test_request_ack(transport, message):
  mq = setup_mq(transport, ack_channel="testing")
  mq.send(message.to, message.payload)

  mq.process_outbox()
  assert len(transport.items) == 1
  assert transport.items[0].tags["ack"] == "testing"

def test_resend_without_ack(transport, message):
  mq = setup_mq(transport, tos=[False, True])
  mq.send(message.to, message.payload)

  mq.process_outbox() # send
  assert len(mq.outbox) == 1

  mq.process_outbox() # defer
  assert len(transport.items) == 1

  mq.process_outbox() # send retry
  assert len(transport.items) == 2

def test_receive_ack(transport, message):
  mq = setup_mq(transport, ack_channel="testing")
  mq.send(message.to, message.payload)
  mq.process_outbox()
  ack = Message("testing", {}, { "ack" : next(mq.outbox).id } )
  transport.send(ack)
  transport.deliver()
  mq.process_inbox()

  assert len(mq.outbox) == 0

def test_give_ack(transport, message, ids):
  mq = setup_mq(transport, ids=ids)
  def accept(msg):
    pass
  mq.on_message("channel", accept)

  msg = Message("channel", "payload", id="abc")
  msg.tags["ack"] = "acks"
  transport.send(msg)
  transport.deliver()
  mq.process_inbox()

  assert len(mq.outbox.messages)           == 1
  assert mq.outbox.messages[1].to          == "acks"
  assert mq.outbox.messages[1].payload     == {}
  assert mq.outbox.messages[1].tags["ack"] == "abc"
