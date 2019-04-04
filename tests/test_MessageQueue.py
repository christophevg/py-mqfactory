import pytest
import time

from mqfactory         import Threaded, MessageQueue
from mqfactory.message import Message

def test_send_message(transport, message):
  mq = MessageQueue(transport)
  mq.send(message.to, message.payload)
  mq.process_outbox()

  transport.send.assert_called_once()
  msg = transport.send.call_args[0][0]
  assert msg.to == message.to
  assert msg.payload == message.payload

def test_receive_message(transport, message):
  mq = MessageQueue(transport)

  delivered = []
  def accept(msg):
    delivered.append(msg)
  mq.on_message(message.to, accept)

  # get store_to_inbox handler
  transport.on_message.assert_called_once()
  to, store_to_inbox = transport.on_message.call_args[0]
  assert to == message.to

  # make a delivery
  store_to_inbox(message)
  mq.process_inbox()

  assert len(delivered) == 1
  assert delivered[0] == message

def test_before_send_wrappers(transport, message):
  mq = MessageQueue(transport)
  
  mq.before_sending.append(number(1))
  mq.before_sending.append(number(2))
  mq.before_sending.append(number(3))

  mq.send(message.to, message.payload)
  mq.process_outbox()

  transport.send.assert_called_once()
  msg = transport.send.call_args[0][0]

  assert msg.to      == "321{0}123".format(message.to)
  assert msg.payload == "321{0}123".format(message.payload)

def test_before_handling_wrappers(transport, message):
  mq = MessageQueue(transport)

  mq.before_handling.append(number(4))
  mq.before_handling.append(number(5))
  mq.before_handling.append(number(6))

  delivered = []
  def accept(msg):
    delivered.append(msg)

  mq.on_message(message.to, accept)
  
  # get store_to_inbox handler
  assert transport.on_message.called
  to, store_to_inbox = transport.on_message.call_args[0]
  assert to == message.to

  # make a delivery
  store_to_inbox(message.copy())
  mq.process_inbox()

  assert len(delivered) == 1
  assert delivered[0].to == "456{0}654".format(message.to)
  assert delivered[0].payload == "456{0}654".format(message.payload)

def test_threaded_outbox_processing(transport, message):
  mq = Threaded(MessageQueue(transport), interval=0.1)

  mq.send(message.to, message.payload)
  time.sleep(0.2) # give processor thread time to be run at least once

  transport.send.assert_called_once()
  msg = transport.send.call_args[0][0]
  assert msg.to == message.to
  assert msg.payload == message.payload

def test_failing_processing(transport, message):
  mq = MessageQueue(transport)
  class SomeException(Exception): pass
  called = []
  def failing_wrapper(mq):
    called.append(True)
    raise SomeException
  mq.before_sending.append(failing_wrapper)
  mq.send(message.to, message.payload)
  mq.process_outbox()
  assert len(called) == 1

# simple message wrapper helper functions

def quotes(msg):
  msg.to      = "'{0}'".format(msg.to)
  msg.payload = "'{0}'".format(msg.payload)
  return msg

def number(number):
  def add_number(msg):
    msg.to      = "{0}{1}{0}".format(number, msg.to)
    msg.payload = "{0}{1}{0}".format(number, msg.payload)
    return msg
  return add_number
