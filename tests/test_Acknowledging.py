import pytest

from mock import Mock, patch

from mqfactory               import DeferException
from mqfactory.transport.qos import check_timeout
from mqfactory.transport.qos import Acknowledging, Acknowledgement

def test_timeout_on_missing_sent_time(message):
  assert check_timeout(message)

@patch("mqfactory.tools.clock.now")
def test_timeout_after_5s(mocked_time, message):
  message.tags["sent"] = 10000
  mocked_time.return_value  = 10001
  assert not check_timeout(message)
  mocked_time.return_value  = 15001
  assert check_timeout(message)

def test_setup_of_acknowledging_aspects(mq):
  ack = Acknowledging(mq, return_ack=True)
  mq.before_sending.append.assert_called_with(ack.request_and_wait)
  mq.after_sending.append.assert_called_with(ack.record_sent_time)
  mq.after_handling.append.assert_called_with(ack.give)

def test_dont_request_ack_on_ack(mq, message):
  ack = Acknowledgement(mq)
  message.to = mq.name + "/ack"
  message.tags["confirm"] = "something"
  ack.request_and_wait(message)
  assert not "ack" in message.tags

def test_requesting_ack(mq, message):
  ack = Acknowledgement(mq)
  ack.request_and_wait(message)
  assert "ack" in message.tags
  assert message.tags["ack"] == mq.name + "/ack"

def test_dont_record_sent_time_on_ack(mq, message):
  ack = Acknowledgement(mq)
  message.to = mq.name + "/ack"
  message.tags["confirm"] = "something"
  ack.record_sent_time(message)
  assert not "sent" in message.tags

@patch("mqfactory.tools.clock.now")
def test_record_sent_time(mocked_time, mq, message):
  mocked_time.return_value = 123
  ack = Acknowledgement(mq,)
  with pytest.raises(DeferException):
    ack.record_sent_time(message)
  assert "sent" in message.tags
  assert message.tags["sent"] == 123

@patch("mqfactory.tools.clock.now")
def test_wait_for_timeout(mocked_time, mq, message):
  ack = Acknowledgement(mq)
  mocked_time.return_value = 1000
  ack.request_and_wait(message)
  with pytest.raises(DeferException):
    ack.record_sent_time(message)
  # wait
  with pytest.raises(DeferException):
    mocked_time.return_value = 2000
    ack.request_and_wait(message)
  # carry on
  mocked_time.return_value = 6100
  ack.request_and_wait(message)

def test_give_ack(mq, message):
  ack = Acknowledgement(mq)
  message.tags["ack"] = "somewhere"
  ack.give(message)
  mq.send.assert_called_with( message.tags["ack"], {}, { "confirm" : message.id } )

def test_dont_give_ack_on_ack(mq, message):
  ack = Acknowledgement(mq)
  message.tags["confirm"] = "somewhere"
  message.to = mq.name + "/ack"
  ack.give(message)
  mq.send.assert_not_called()

def test_handling_of_acks(mq, message):
  ack = Acknowledgement(mq)
  mq.on_message.assert_called_with(ack.ack_channel, ack.handle)
  message.tags["confirm"] = "some message id"
  mq.outbox.__getitem__.return_value = "some message object"
  ack.handle(message)
  mq.outbox.remove.assert_called_with("some message object")

def test_not_handling_of_unknown_message_to_ack(mq, message):
  ack = Acknowledgement(mq)
  mq.on_message.assert_called_with(ack.ack_channel, ack.handle)
  message.tags["confirm"] = "some message id"
  mq.outbox.__getitem__.side_effect = KeyError()
  ack.handle(message)
  mq.outbox.remove.assert_not_called()
