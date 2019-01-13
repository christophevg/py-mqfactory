import time

from mqfactory import Threaded, MessageQueue

from . import TransportMock

def test_send_message(message):
  transport = TransportMock()
  mq = MessageQueue(transport)
  mq.send(*message)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0] == tuple(message)

def test_receive_message(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  delivered = []
  def accept(mq, to, payload):
    delivered.append((mq,) + tuple(message))
  mq.on_message(message.to, accept)
  
  transport.items.append(tuple(message))
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0] == (mq,) + tuple(message)

def test_single_send_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  def quotes(to, payload):
    return ("'{0}'".format(to), "'{0}'".format(payload))
  mq.before_sending.append(quotes)

  mq.send(*message)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0] == quotes(*message)

def test_multiple_send_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)
  
  def number(number):
    def add_number(to, payload):
      return (
        "{0}{1}{0}".format(number, to),
        "{0}{1}{0}".format(number, payload)
      )
    return add_number
  mq.before_sending.append(number(1))
  mq.before_sending.append(number(2))
  mq.before_sending.append(number(3))

  mq.send(*message)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0] == (
    "321{0}123".format(message.to),
    "321{0}123".format(message.payload)
  )

def test_single_receive_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  def quotes(to, payload):
    return ("'{0}'".format(to), "'{0}'".format(payload))
  mq.after_receiving.append(quotes)

  delivered = []
  def accept(mq, to, payload):
    delivered.append((mq, to, payload))

  mq.on_message(message.to, accept)
  
  transport.items.append(message)
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0][1:] == quotes(*message)

def test_multiple_receive_wrapper(message):
  transport = TransportMock()
  mq = MessageQueue(transport)

  def number(number):
    def add_number(to, payload):
      return (
        "{0}{1}{0}".format(number, to),
        "{0}{1}{0}".format(number, payload)
      )
    return add_number
  mq.after_receiving.append(number(1))
  mq.after_receiving.append(number(2))
  mq.after_receiving.append(number(3))

  delivered = []
  def accept(mq, to, payload):
    delivered.append((mq, to, payload))

  mq.on_message(message.to, accept)
  
  transport.items.append(message)
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0] == (
    mq,
    "321{0}123".format(message.to),
    "321{0}123".format(message.payload)
  )

def test_threaded_outbox_processing(message):
  transport = TransportMock()
  mq = Threaded(MessageQueue(transport), interval=0.1)

  mq.send(*message)
  time.sleep(0.2) # give processor thread time to be run at least once

  assert len(transport.items) == 1
  assert transport.items[0] == tuple(message)
