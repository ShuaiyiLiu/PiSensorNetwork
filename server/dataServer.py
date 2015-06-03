""" This is the data server of PiSensorNetwork """

from twisted.internet.defer import Deferred
from twisted.internet.protocol import ServerFactory
from twisted.internet import protocol
from twisted.enterprise import adbapi
from twisted.python import log
from twisted.internet.task import LoopingCall
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
WORKING = 0
NOTRESPONDING = 1
EXCEPTION = 2
STATE_REFRESH_TIME = 5 
STATES = ["WORKING", "NOTRESPONDING", "EXCEPTION"]
MAX_INTERVAL = 15 # nodes are considered as NOTRESPONDING if no message from
                  # them for more than MAX_INTERVAL
nsm = {}
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

class MapNodeState(DBObject):
    """Class for map_nodeState table."""
    TABLENAME = 'map_nodeState'

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
            self.dbInsert(dcts[:-1], clientip) # the last element is datatype
        elif (dataType == "register"):
            self.dbRegister(dcts[:-1], clientip)
        elif (dataType == "exception"):
            self.nodeException(dcts[:-1])
        elif (dataType == "upload_request"):
            self.requestHandler(dcts[:-1])
        else:
            message = "Data type {} from {} cannot be recognized!".format(
                    dataType, clientip)
            self.transport.write(message)
            myObserver.msg(message, logLevel = logging.DEBUG)
            self.transport.loseConnection()
    
    def nodeException(self, dcts):
        """Handle node exception"""
        global nsm
        nodeID = dcts[0]["node_id"]
        nsm[nodeID] = ["EXCEPTION", datetime.datetime.now()]
        myObserver.msg("Exception from node {}.".format(nodeID), logLevel =
                logging.WARNING)

    def _dbRegisterRespond(self, transaction, nodeName, ip):
        global nsm
        transaction.execute("""INSERT INTO map_node (name, ip) 
                            VALUES (%s, %s)""", (nodeName, ip))
        # TODO: Here we always insert a row in table map_nodeVersion, but once
        # how lon/lat works is figured out, nodeVersion should be updated 
        # only when lon/lat is changed. 
        nodeID = transaction.lastrowid
        self.transport.write("""SUCCESS! Your ID is {}""".
                format(nodeID))
        transaction.execute("""INSERT INTO map_nodeVersion (node_id, longitude,
                            latitude) VALUES
                            (%s, %s, %s)""", (nodeID, 0, 0))
        transaction.execute("""INSERT INTO map_nodeState (node_id, status)
                            VALUES (%s, %s)""", (nodeID,
                                "NOTRESPONDING"))
        myObserver.msg("{} has successfully registered".
                format(nodeName), logLevel = logging.INFO)
        self.transport.loseConnection()
        nsm[nodeID] = [NOTRESPONDING, datetime.datetime.now()]
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
    
    def _dbInsertData(self, version_id, dcts, ip, nodeID):

        def dbData(transaction, dcts):
            data_id = 0
            temperature = 20
            humidity = 5
            for dct in dcts:
                value = dct["value"]
                value_name = dct["value_name"]
                if dct.has_key("time"):
                    collect_time = dct["time"]
                if value_name == "Temperature":
                    temperature = value
                elif value_name == "Humidity":
                    humidity = value
                elif value_name == "DataID":
                    data_id = value
                    creat_time = str(datetime.datetime.now())
                    transaction.execute("""INSERT INTO map_data (temperature, 
                            humidity, version_id, collect_time, data_id, 
                            creat_time) VALUES (%s, %s, %s, %s, %s, %s)""",
                            (temperature, humidity, version_id, collect_time,
                                data_id, creat_time))
            return data_id
        
        def sendBackDataID(data_id):
            self.transport.write("Upload Successful! " + 
                "Requested data ID is {}".format(data_id+1))
            self.transport.loseConnection()

        dbpool.runInteraction(dbData, dcts).addCallback(sendBackDataID)               

        def updateIP(transaction, ip):
            transaction.execute("""UPDATE map_node SET ip = %s WHERE node_id =
                    %s""", (ip, nodeID))
        dbpool.runInteraction(updateIP, ip)

    def dbInsert(self, dcts, ip):
        """
        Insert environmental data received from nodes to database.
        """
        global nsm
        nodeID = dcts[0]["node_id"]
        # d, a deferred is already fired, and rows in nodeversion table will be
        # returned to callbacks added to d
        d = MapNodeVersion.find(where = ["node_id = ?", nodeID], 
                                orderby = "version_id DESC", limit = 1)
        d.addCallback(lambda vid: self._dbInsertData(vid.version_id, dcts[1:], ip, nodeID))
        nsm[nodeID] = [nsm[nodeID][0], datetime.datetime.now()]
        myObserver.msg("Data from node with ID: {} has been stored".
                format(nodeID), logLevel = logging.DEBUG)

    def _sendRequestedDataID(self, latestData):
        lastDataId = 1
        if latestData is None:
            self.transport.write("requested data ID is 1")
        else:
            lastDataId = latestData.data_id
            self.transport.write("requested data ID is {}".format(lastDataId + 1))
        self.transport.loseConnection()
        return lastDataId + 1

    def sendRequestedDataID(self, nodeVersion, nodeID):
        if nodeVersion is None:
            self.transport.write("Node version does not exsits. Try re-register?")
            self.transport.loseConnection()
            return
        version_id = nodeVersion.version_id
        d = MapData.find(where = ["version_id = ?", version_id],
                         orderby = "data_id DESC", limit = 1)
        d.addCallback(lambda res: self._sendRequestedDataID(res))
        return d

    def requestHandler(self, dcts):
        "Handle the upload_request datatype by sending nodes their requested data id."
        nodeID = dcts[0]["node_id"]
        d = MapNodeVersion.find(where = ["node_id = ?", nodeID],
                                orderby = "version_id DESC", limit = 1)
        d.addCallback(lambda res: self.sendRequestedDataID(res, nodeID))

    def connectionLost(self, reason):
        pass

class DataServerFactory(ServerFactory):
    """
    Factory of data server.
    """
    protocol = DataServerProtocol

def dbUpdateStates(transaction, nodeID, state):
    transaction.execute("""INSERT INTO map_nodeState (node_id, status)
                        VALUES (%s, %s) ON DUPLICATE KEY UPDATE status =
                        VALUES(status)""", (nodeID,
                        state))

def stateMonitor():
    """
    Monitor of nodes' heart beats.
    """
    import MySQLdb
    from contextlib import closing
    global nsm
    with open("server.json") as serverCfgFile:
        dbCfg = json.load(serverCfgFile)["database"]
        db = MySQLdb.connect(db = dbCfg["db"], user = dbCfg["user"])
    for nodeID in nsm.keys():
        curTime = datetime.datetime.now()
        diffTime = (curTime - nsm[nodeID][1]).total_seconds()
        refreshed = False
        if nsm[nodeID][0] == WORKING and diffTime > MAX_INTERVAL:
            nsm[nodeID][0] = NOTRESPONDING
            myObserver.msg(
                "Node({})'s state is changed from WORKING to ".format(nodeID) + 
                "NOTRESPONDING.")
            refreshed = True
        elif nsm[nodeID][0] == NOTRESPONDING and diffTime < MAX_INTERVAL:
            nsm[nodeID][0] = WORKING
            myObserver.msg(
                "Node({})'s state is changed from NOTRESPONDING to ".format(nodeID) + 
                "WORKING.")
            refreshed = True
        elif nsm[nodeID][0] == EXCEPTION and diffTime < MAX_INTERVAL:
            nsm[nodeID][0] = WORKING
            myObserver.msg(
                "Node({})'s state is changed from EXCEPTION to ".format(nodeID) + 
                "WORKING.")
            refreshed = True

        if refreshed:
            dbpool.runInteraction(dbUpdateStates, nodeID, STATES[nsm[nodeID][0]])

def getNodesFromDB():
    import MySQLdb
    from contextlib import closing
    global nsm
    with open("server.json") as serverCfgFile:
        dbCfg = json.load(serverCfgFile)["database"]
        db = MySQLdb.connect(db = dbCfg["db"], user = dbCfg["user"])
    with closing(db.cursor()) as cur:
        cur.execute("""SELECT * FROM map_node;""")
        nodes = cur.fetchall()
        for node in nodes:
            curTime = datetime.datetime.now()
            nsm[node[0]] = [NOTRESPONDING, curTime.replace(2000)]
    db.close()

def main():
    from twisted.internet import reactor
    factory = DataServerFactory()
    port = reactor.listenTCP(PORT, factory)
    myObserver.startLogging(sys.stdout)
    nsm = getNodesFromDB()
    # TODO: assign a new name to log file everytime.
    myObserver.addObserver(myObserver.MyFileLogObserver(file("log", "w")).emit)
    myObserver.msg("Data Server Running at port {} now.".format(PORT),
            logLevel=logging.INFO)
    loopObj = LoopingCall(stateMonitor)
    loopObj.start(STATE_REFRESH_TIME, now=True)
    reactor.run()

if __name__ == "__main__":
    main()

