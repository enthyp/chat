import time
import random
from ai.model import Model


class MockChecker(Model):
    def __init__(self):
        self.keywords = ['foo', 'bar']

    def process(self, msg):
        time.sleep(1.2 * random.random())
        return [int(kw in msg) for kw in self.keywords]
