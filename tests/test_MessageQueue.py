import time

from mqfactory import Message, Threaded, MessageQueue

from . import TransportMock

def test_send_message(message):
  transport = TransportMock()
  mq = MessageQueue(transport)
  mq.send(message.to, message.payload)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0].to == message.to
  assert transport.items[0].payload == message.payload

def test_receive_message(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  delivered = []
  def accept(msg):
    delivered.append(msg)
  mq.on_message(message.to, accept)
  
  transport.items.append(message)
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0] == message

def test_single_send_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  mq.before_sending.append(quotes)

  mq.send(message.to, message.payload)
  mq.process_outbox()

  assert len(transport.items) == 1
  quotes(message)
  assert transport.items[0].to == message.to
  assert transport.items[0].payload == message.payload

def test_multiple_send_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)
  
  mq.before_sending.append(number(1))
  mq.before_sending.append(number(2))
  mq.before_sending.append(number(3))

  mq.send(message.to, message.payload)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0].to      == "321{0}123".format(message.to)
  assert transport.items[0].payload == "321{0}123".format(message.payload)

def test_single_receive_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  mq.after_receiving.append(quotes)

  delivered = []
  def accept(msg):
    delivered.append(msg)

  mq.on_message(message.to, accept)
  
  transport.items.append(Message(message.to, message.payload))
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0].to      == "'{0}'".format(message.to)
  assert delivered[0].payload == "'{0}'".format(message.payload)

def test_multiple_receive_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  mq.after_receiving.append(number(1))
  mq.after_receiving.append(number(2))
  mq.after_receiving.append(number(3))

  delivered = []
  def accept(msg):
    delivered.append(msg)

  mq.on_message(message.to, accept)
  
  transport.items.append(Message(message.to, message.payload))
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0].to == "123{0}321".format(message.to)
  assert delivered[0].payload == "123{0}321".format(message.payload)

def test_threaded_outbox_processing(message):
  transport = TransportMock()
  mq = Threaded(MessageQueue(transport), interval=0.1)

  mq.send(message.to, message.payload)
  time.sleep(0.2) # give processor thread time to be run at least once

  assert len(transport.items) == 1
  assert transport.items[0].to == message.to
  assert transport.items[0].payload == message.payload

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
