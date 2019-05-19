class Channel:
    def __init__(self, name=None):
        self.name = name
        self.peers = set()
        self.users = set()

    def register_peer(self, peer):
        self.peers.add(peer)

    def unregister_peer(self, peer):
        self.peers.remove(peer)

    def publish(self, author, message):
        for peer in self.peers - {author}:
            peer.receive(message)

    def names(self):
        return list(self.users)
