import time
import logging

# provide simple access to time in milliseconds

class Millis(object):
  def now(self):
    return int(round(time.time() * 1000))
clock = Millis()

# helper function to apply a list of functions to an object

def wrap(msg, wrappers):
  for wrapper in wrappers: wrapper(msg)

