import sys
import logging

from mqfactory import DeferException, millis
from mqfactory.message import Message

'''
Acknowledgment works in several phases:
- when used, a subscription on an ack channel is made
- when sending a message, an "ack" tag is added, containing the ack channel
- after sending the message, the send message is added back to the outbox with
  a timestamp
- if the message is ready to be send again, but the time since sending it hasn't
  surpassed a timeout, sending is defered
- if the message is ready to be send again, and the the timeout has passed, it
  is just send again
- if an acknowledgement is received, the corresponding message is removed
'''

def check_timeout(message):
  if not "sent" in message.tags: return True # not sent == send it!
  return millis() - message.tags["sent"] >= 5000

class Acknowledgement(object):
  def __init__(self, mq, timedout=check_timeout, ack_channel="/ack", clock=millis):
    self.mq = mq
    self.timedout = timedout
    self.ack_channel = ack_channel
    self.clock = clock
    self.mq.on_message(self.ack_channel, self.handle)
    
  def request(self, message):
    # add the "ack" tag to request an acknowledgement
    if not "ack" in message.tags:
      message.tags["ack"] = self.ack_channel
      logging.debug("requesting ack for {0}".format(message.tags["id"]))
    else:
      # if the ack tag was already added, we might want to resend it
      if not self.timedout(message):
        raise DeferException

  def wait(self, message):
    # don't add retry for acknowledgements themselves
    if not message.to == self.ack_channel:
      retry = message.copy()
      retry.tags["sent"] = self.clock()
      logging.debug("scheduling retry for {0}".format(retry.tags["id"]))
      self.mq.outbox.append(retry)

  def give(self, message):
    if "ack" in message.tags and not message.to == self.ack_channel:
      logging.debug("acknowledging {0}".format(message.tags["id"]))
      self.mq.send( message.tags["ack"], {}, { "ack" : message.tags["id"] } )

  def handle(self, message):
    logging.debug("received ack for {0}".format(message.tags["ack"]))
    def acked_message(m):
      return m.tags["id"] == message.tags["ack"]

    try:
      self.mq.outbox.pop(self.mq.outbox.index(acked_message))
      logging.debug("popped acked msg {0}".format(message.tags["ack"]))
    except ValueError:
      logging.warn("unknown message ack {0}".format(message.tags["ack"]))
      sys.exit(1)

def Acknowledging(mq, ack=None, clock=millis, timedout=check_timeout):
  acknowledgement = ack or Acknowledgement(mq, clock=clock, timedout=timedout)
  mq.before_sending.append(acknowledgement.request)
  mq.after_sending.append(acknowledgement.wait)
  mq.after_handling.append(acknowledgement.give)
  return mq
