import sys
import logging

from mqfactory         import DeferException
from mqfactory.tools   import clock
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
  return clock.now() - message.tags["sent"] >= 5000

class Acknowledgement(object):
  def __init__(self, mq, ack_channel="ack"):
    self.mq = mq
    self.ack_channel = self.mq.name + "/" + ack_channel
    self.mq.on_message(self.ack_channel, self.handle)
  
  def log(self, msg, level=logging.info):
    level("{0}: {1}".format(self.mq.name, msg))
    
  def request_and_wait(self, message):
    # don't do anything special for ack messages
    if "confirm" in message.tags: return

    # add the "ack" tag to request an acknowledgement and continue sending it
    if not "ack" in message.tags:
      message.tags["ack"] = self.ack_channel
      self.log("requesting ack for {0}".format(message.id))
    else:
      # the ack tag is present, so this message was sent already at least once
      # check for timeout and let it be sent again, or Defer until timeout
      if not check_timeout(message):
        logging.debug("DEFER: message ack was previously requests, but not long enough to resend")
        raise DeferException
      self.log("need to resend message {0}".format(message.id))

  def record_sent_time(self, message):
    # don't do anything special for ack messages, simple let it be deleted
    if "confirm" in message.tags: return
    # record sent time
    message.tags["sent"] = clock.now()
    logging.debug("DEFER: scheduling retry for {0}".format(message.id))
    raise DeferException

  def give(self, message):
    if "ack" in message.tags:
      self.log("acknowledging {0}".format(message.id))
      self.mq.send( message.tags["ack"], {}, { "confirm" : message.id } )

  def handle(self, message):
    self.log("got ack for {0}".format(message.tags["confirm"]))
    try:
      self.mq.outbox.remove(self.mq.outbox[message.tags["confirm"]])
      logging.debug("popped acked msg {0}".format(message.tags["confirm"]))
    except KeyError:
      logging.warning("unknown message ack {0}".format(message.tags["confirm"]))

def Acknowledging(mq, ack=None, return_ack=False):
  acknowledgement = ack or Acknowledgement(mq)
  mq.before_sending.append(acknowledgement.request_and_wait)
  mq.after_sending.append(acknowledgement.record_sent_time)
  mq.after_handling.append(acknowledgement.give)
  return acknowledgement if return_ack else mq
