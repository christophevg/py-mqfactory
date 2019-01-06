import time
import random
import string

from mqfactory import Threaded, MessageQueue

from . import TransportMock

def make_message():
  def generate_string(length=10):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
  return (generate_string(), generate_string())

def test_send_message():
  transport = TransportMock()
  mq = MessageQueue(transport)
  (to, payload) = make_message()

  mq.send(to, payload)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0] == (to, payload)

def test_receive_message():
  transport = TransportMock()
  mq = MessageQueue(transport)
  (to, payload) = make_message()

  delivered = []
  def accept(mq, to, payload):
    delivered.append((mq, to, payload))
  mq.on_message(to, accept)
  
  transport.items.append((to, payload))
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0] == (mq, to, payload)

def test_single_send_wrapper():
  transport = TransportMock()
  mq = MessageQueue(transport)
  (to, payload) = make_message()

  def quotes(to, payload):
    return ("'{0}'".format(to), "'{0}'".format(payload))
  mq.before_sending.append(quotes)

  mq.send(to, payload)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0] == quotes(to, payload)

def test_multiple_send_wrapper():
  transport = TransportMock()
  mq = MessageQueue(transport)
  (to, payload) = make_message()
  
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

  mq.send(to, payload)
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0] == (
    "321{0}123".format(to),
    "321{0}123".format(payload)
  )

def test_single_receive_wrapper():
  transport = TransportMock()
  mq = MessageQueue(transport)
  (to, payload) = make_message()

  def quotes(to, payload):
    return ("'{0}'".format(to), "'{0}'".format(payload))
  mq.after_receiving.append(quotes)

  delivered = []
  def accept(mq, to, payload):
    delivered.append((mq, to, payload))

  mq.on_message(to, accept)
  
  transport.items.append((to, payload))
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0][1:] == quotes(to, payload)

def test_multiple_receive_wrapper():
  transport = TransportMock()
  mq = MessageQueue(transport)
  (to, payload) = make_message()

  def add_number(number):
    def add_numbers(to, payload):
      return (
        "{0}{1}{0}".format(number, to),
        "{0}{1}{0}".format(number, payload)
      )
    return add_numbers
  mq.after_receiving.append(add_number(1))
  mq.after_receiving.append(add_number(2))
  mq.after_receiving.append(add_number(3))

  delivered = []
  def accept(mq, to, payload):
    delivered.append((mq, to, payload))

  mq.on_message(to, accept)
  
  transport.items.append((to, payload))
  transport.deliver()

  assert len(delivered) == 1
  assert delivered[0] == (
    mq,
    "321{0}123".format(to),
    "321{0}123".format(payload)
  )

def test_threaded_outbox_processing():
  transport = TransportMock()
  mq = Threaded(MessageQueue(transport), interval=0.1)
  (to, payload) = make_message()

  mq.send(to, payload)
  time.sleep(0.1) # give processor thread time to be run at least once

  assert len(transport.items) == 1
  assert transport.items[0] == (to, payload)
