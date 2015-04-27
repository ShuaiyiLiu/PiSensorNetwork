""" Json Receiver Protocol used by server"""

from twisted.internet import protocol

class PiJsonReceiver(protocol.Protocol):
    """
    A protocol that receives customized json data: json data followed by
    '/r/n/r/n' indicating the end of message. And transform the json data to a
    dictionary.
    """
    
    def makeConnection(self, transport):
        """
        Initializes the protocol.
        """
        protocol.Protocol.makeConnection(self, transport)
        self._remainingData = ""


    def dataReceived(self, data):
        """
        Receives some characters of a customized json file.

        Whenever a complete json is received, this method extracts
        it and calls L{dictReceived} to process it.
        """
        self._remainingData += data
        if data:
            try:
                self._consumeData()
            except IncompleteCustomizedJson:
                pass 
            except ValueError:
                self._handleParseError()
    
    
    def dictReceived(self, dct):
        """
        Override this for notification when each complete dictionary is
        tranformed.
        """

        raise NotImplementedError()
        
    
    def _consumeData(self):
        """
        Consume the content of C{self._remainingData}.
        """
        if self._remainingData.endswith('\r\n\r\n'):
            try:
                import json
                dct = json.loads(self._remainingData[0:-4])
                self.dictReceived(dct)
                self.transport.loseConnection()
            except ValueError:
                raise ValueError
        else:
            raise IncompleteCustomizedJson
    

    def _handleParseError(self):
        """
        Terminates the connection and print the error.
        """
        print 'received json data parsed error!'
        self.transport.loseConnection()


class IncompleteCustomizedJson(Exception):
    """
    Not enough data to complete a customized json.
    """


