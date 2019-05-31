class Channel:
    def __init__(self, name=None):
        self.name = name
        self.client_peers = set()
        self.server_peers = set()
        self.users = set()

    def register_peer(self, peer, nick=None):
        if nick:
            self.client_peers.add(peer)
            self.users.add(nick)
        else:
            self.server_peers.add(peer)

    def unregister_peer(self, peer, nick=None):
        if nick:
            self.client_peers.remove(peer)
            self.users.remove(nick)
        else:
            self.server_peers.remove(peer)

    def publish(self, author, message, to):
        if to == 'all':
            peers = self.client_peers | self.server_peers
        elif to == 'clients':
            peers = self.client_peers
        elif to == 'servers':
            peers = self.server_peers
        else:
            return

        for peer in peers - {author}:
            peer.receive(message)

    def names(self):
        return list(self.users)
