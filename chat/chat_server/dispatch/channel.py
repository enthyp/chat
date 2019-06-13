class Channel:
    def __init__(self, dispatcher, name):
        self.dispatcher = dispatcher
        self.name = name
        self.users = set()

    def register_user(self, nick):
        self.users.add(nick)

    def unregister_user(self, nick):
        self.users.discard(nick)

    def publish(self, author, message, locally=False):
        peers = self.dispatcher.get_peers(self.users, locally)

        for peer in peers - {author}:
            peer.receive(message)

    def names(self):
        return self.users
