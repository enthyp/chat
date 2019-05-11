class Channel:
    def __init__(self, name):
        self.name = name
        self.subscribers = set()

    def register_subscriber(self, subscriber):
        self.subscribers.add(subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.remove(subscriber)

    def publish(self, message):
        for sub in self.subscribers:
            sub.handle_message(self.name, message)
