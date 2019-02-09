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
      print answers[0]
      return answers.pop(0)
    except IndexError:
      return False
  return f

def setup_mq(transport, tos=[], ack_channel="testing"):
  mq  = MessageQueue(transport)
  ack = Acknowledgement(mq, timedout=mocked_to(tos), ack_channel=ack_channel)
  return Acknowledging(mq, ack=ack)

def test_request_ack(transport, message):
  mq = setup_mq(transport, ack_channel="testing")
  mq.send(message.to, message.payload)

  mq.process_outbox()
  assert len(transport.items) == 1
  assert transport.items[0].tags["ack"]["to"] == "testing"

def test_resend_without_ack(transport, message):
  mq = setup_mq(transport, tos=[False, True])
  mq.send(message.to, message.payload)

  mq.process_outbox() # send
  assert len(mq.outbox.items) == 1

  mq.process_outbox() # defer
  assert len(transport.items) == 1

  mq.process_outbox() # send retry
  assert len(transport.items) == 2

def test_receive_ack(transport, message):
  mq = setup_mq(transport, ack_channel="testing")
  mq.send(message.to, message.payload)
  mq.process_outbox()
  id = mq.outbox.items[0].tags["ack"]["id"]
  ack = Message("testing", {}, { "ack" : { "id" : id } } )
  transport.send(ack)
  transport.deliver()

  assert len(mq.outbox.items) == 0

def test_give_ack(transport, message):
  mq = setup_mq(transport)
  delivered = []
  def accept(msg):
    delivered.append(msg)
  mq.on_message("channel", accept)

  msg = Message("channel", "payload")
  msg.tags["ack"] = { "id" : "abc", "to": "ack" }
  transport.send(msg)
  transport.deliver()

  assert len(mq.outbox.items) == 1
  assert mq.outbox.items[0].to == "ack"
  assert mq.outbox.items[0].tags == { "ack" : {"id" : "abc"} }
