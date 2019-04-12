from server.ai.model import Model


class Checker(Model):
    def __init__(self):
        self.keywords = ['honkey', 'honkie']

    def process(self, msg):
        return [int(kw in msg) for kw in self.keywords]
