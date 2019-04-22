import time

# provide simple access to time in milliseconds

class Millis(object):
  def now(self):
    return int(round(time.time() * 1000))
clock = Millis()

# helper function to apply a list of functions to an object

def wrap(msg, wrappers):
  for wrapper in wrappers: wrapper(msg)

# basic first-match Policy

class Rule(object):
  def __init__(self, pattern={}, value=None):
    self.pattern = pattern
    self.value   = value

  def matches(self, instance):
    for key, value in self.pattern.items():
      try: assert self.match(instance[key], value)
      except: return False
    return True

  def match(self, actual, expected):
    return actual == expected

CATCH_ALL = Rule({}, None)

class Policy(object):
  def __init__(self, rules=[]):
    self.rules = rules

  def match(self, instance):
    return next((rule for rule in self.rules if rule.matches(instance)), CATCH_ALL)
