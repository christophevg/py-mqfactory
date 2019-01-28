import pytest

from . import generate_random_string

class RandomMessage(object):
  def __init__(self):
    self.to      = generate_random_string()
    self.payload = generate_random_string()
    self.tags    = {}

  def __getitem__(self, index):
    return [self.to, self.payload][index]

  def __iter__(self):
    yield ("to",      self.to)
    yield ("payload", self.payload)
    return

@pytest.fixture
def message():
  return RandomMessage()
