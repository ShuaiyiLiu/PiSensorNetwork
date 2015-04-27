""" This is the data server of PiSensorNetwork """

from twisted.internet.defer import Deferred
from twisted.internet.protocol import ServerFactory
from twisted.internet import protocol
from piJsonReceiver import PiJsonReceiver

HOST = '127.0.0.1'
PORT = 8686

class DataServerProtocol(PiJsonReceiver):
    """
    Protocol used by data server. 
    """

    def dictReceived(self, dct):
        print dct

class DataServerFactory(ServerFactory):
    """
    Factory of data server.
    """
    protocol = DataServerProtocol

def main():
    from twisted.internet import reactor
    factory = DataServerFactory()
    port = reactor.listenTCP(PORT, factory)
    reactor.run()

if __name__ == "__main__":
    main()


