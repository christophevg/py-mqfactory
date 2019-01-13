import pytest
import random
import string

class RandomMessage(object):
  def __init__(self):
    self.to      = self.generate_string()
    self.payload = self.generate_string()
  def generate_string(self, length=10):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
  def __getitem__(self, index):
    return [self.to, self.payload][index]
  def __iter__(self):
    yield self.to
    yield self.payload

@pytest.fixture
def message():
  return RandomMessage()