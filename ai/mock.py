import time
import random
from .model import Model


class Checker(Model):
    def __init__(self):
        self.keywords = ['foo', 'bar']

    def process(self, msg):
        time.sleep(1.2 * random.random())
        return [int(kw in msg) for kw in self.keywords]
