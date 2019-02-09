import copy
import pytest

from . import generate_random_string
from . import TransportMock, StoreMock

class RandomMessage(object):
  def __init__(self):
    self.to      = generate_random_string()
    self.payload = generate_random_string()
    self.tags    = {}

  def copy(self):
    c = RandomMessage()
    c.to = self.to
    c.payload = self.payload
    c.tags = copy.deepcopy(self.tags)
    return c

  def __getitem__(self, index):
    return [self.to, self.payload][index]

  def __iter__(self):
    yield ("to",      self.to)
    yield ("payload", self.payload)
    return

@pytest.fixture
def message():
  return RandomMessage()

@pytest.fixture
def transport():
  return TransportMock()

@pytest.fixture
def store():
  return StoreMock({ "collection": {} })

@pytest.fixture
def collection(store):
  return store["collection"]
