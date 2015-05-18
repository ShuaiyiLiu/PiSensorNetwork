""" This is the data server of PiSensorNetwork """

from twisted.internet.defer import Deferred
from twisted.internet.protocol import ServerFactory
from twisted.internet import protocol
from twisted.enterprise import adbapi
from twisted.python import log
from twistar.registry import Registry
from twistar.dbobject import DBObject
from piJsonReceiver import PiJsonReceiver
import json
import datetime
import logging
import sys
import myObserver

HOST = '127.0.0.1'
PORT = 8686

# database connection
dbpool = None
with open("server.json") as serverCfgFile:
    dbCfg = json.load(serverCfgFile)["database"]
    Registry.DBPOOL = adbapi.ConnectionPool(dbCfg["module"],
             db = dbCfg["db"],
             user = dbCfg["user"])
    dbpool = Registry.DBPOOL

class MapNode(DBObject):
    """Class for map_node table."""
    TABLENAME = 'map_node'

class MapNodeVersion(DBObject):
    """Class for map_nodeVersion table."""
    TABLENAME = 'map_nodeVersion'

class MapData(DBObject):
    """Class for map_data table."""
    TABLENAME = 'map_data'

class DataServerProtocol(PiJsonReceiver):
    """
    Protocol used by data server. 
    """
    def dictsReceived(self, dcts):
        try:
            dataType = dcts[-1]
        except Exception as e:
            myObserver.msg("Invalid data received")
            self.transport.write("Invalid data.")
            self.transport.loseConnection()
            raise e
        clientip = self.transport.getPeer().host
        myObserver.msg("Data Received from {}.".format(clientip), logLevel =
                logging.DEBUG)
        if (dataType == "upload"):
            self.dbInsert(dcts[:-1]) # the last element is datatype
        elif (dataType == "register"):
            self.dbRegister(dcts[:-1], clientip)
        else:
            message = "Data type {} from {} cannot be recognized!".format(
                    dataType, clientip)
            self.transport.write(message)
            myObserver.msg(message, logLevel = logging.DEBUG)
            self.transport.loseConnection()
    
    def _dbRegisterRespond(self, transaction, nodeName, ip):
        transaction.execute("""INSERT INTO map_node (name, ip) 
                            VALUES (%s, %s)""", (nodeName, ip))
        # TODO: Here we always insert a row in table map_nodeVersion, but once
        # how lon/lat works is figured out, nodeVersion should be updated 
        # only when lon/lat is changed. 
        self.transport.write("""SUCCESS! Your ID is {}""".
                format(transaction.lastrowid))
        transaction.execute("""INSERT INTO map_nodeVersion (node_id, longitude,
                            latitude) VALUES
                            (%s, %s, %s)""", (transaction.lastrowid, 0, 0))
        myObserver.msg("{} has successfully registered".
                format(nodeName), logLevel = logging.INFO)
        self.transport.loseConnection()
        return True

    def dbRegisterRespond(self, res, nodeName, ip):
        if res:
            # already exists
            myObserver.msg("Failed to register for {}:".format(nodeName) + 
                    "node name already exists", logLevel =
                    logging.INFO)
            self.transport.write("Failed! Node name already exists.")
            self.transport.loseConnection()
        else:
            dbpool.runInteraction(self._dbRegisterRespond, nodeName, ip)

    def dbRegister(self, dcts, ip):
        """
        Handle register request from node.
        """
        nodeName = dcts[0]["name"]
        d = MapNode.exists(where = ['name = ?', nodeName])
        d.addCallback(lambda res: self.dbRegisterRespond(res, nodeName, ip))
    
    def _dbInsertData(self, version_id, dcts):
        mapData = MapData()
        mapData.temperature = 20 # defalut 
        mapData.humidity = 5
        for dct in dcts:
            value = dct["value"]
            value_name = dct["value_name"]
            mapData.collect_time = dct["time"]
            if value_name == "temperature":
                mapData.temperature = value
            elif value_name == "humidity":
                mapData.humidity = value
        mapData.creat_time = str(datetime.datetime.now())
        def done(foo):
            self.transport.write("Data Upload Succeeded!")
            self.transport.loseConnection()
        mapData.save().addCallback(done)

    def dbInsert(self, dcts):
        """
        Insert environmental data received from nodes to database.
        """
        nodeID = dcts[0]["node_id"]
        # d, a deferred is already fired, and rows in nodeversion table will be
        # returned to callbacks added to d
        d = MapNodeVersion.find(where = ["node_id = ?", nodeID], 
                                orderby = "version_id DESC")
        d.addCallback(lambda vid: self._dbInsertData(vid, dcts[1:]))
        myObserver.msg("Data from node with ID: {} has been stored".
                format(nodeID), logLevel = logging.DEBUG)
        
    def connectionLost(self, reason):
        pass

class DataServerFactory(ServerFactory):
    """
    Factory of data server.
    """
    protocol = DataServerProtocol

def main():
    from twisted.internet import reactor
    factory = DataServerFactory()
    port = reactor.listenTCP(PORT, factory)
    myObserver.startLogging(sys.stdout)
    myObserver.addObserver(myObserver.MyFileLogObserver(file("log", "w")).emit)
    myObserver.msg("Data Server Running at port {} now.".format(PORT),
            logLevel=logging.INFO)
    reactor.run()

if __name__ == "__main__":
    main()

