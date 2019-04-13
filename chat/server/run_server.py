# For testing purposes only. It makes both chat server and
# ML service run in the same process which makes Twisted redundant.
from ai_service import service_main
from chat_server import server_main

# TODO: try docker-compose (with queue).

if __name__ == '__main__':
    service_main(10001, True)
<<<<<<< Updated upstream:chat/run_server.py
    server_main(10000, 10001, 0, True, True)
=======
    server_main(10000, 10001, 2, True)
>>>>>>> Stashed changes:chat/server/run_server.py

    from twisted.internet import reactor
    reactor.run()
