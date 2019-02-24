import time
import logging

# provide simple access to time in milliseconds

class Millis(object):
  def now(self):
    return int(round(time.time() * 1000))
clock = Millis()

# helper function to apply a list of functions to an object

indent = -1

def wrap(msg, wrappers):
  global indent
  indent += 1
  for wrapper in wrappers:
    logging.debug("{0} wrap start: {1}".format("."*indent,wrapper))
    wrapper(msg)
    logging.debug("{0} wrap stop : {1}".format("."*indent,wrapper))
  indent -= 1