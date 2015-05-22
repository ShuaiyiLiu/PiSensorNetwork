'''
Module run by each node.
'''

import datetime
import json
import string
import time
import os
import upload
import threading
import SocketServer
import logging

PORT = 9999 # port for receiving commands from ctlServer. 
intervalTime = 5
logging.basicConfig(format='%(asctime)s <%(levelname)s> %(message)s', level=logging.DEBUG)
logs = []

def loggingSave(msg, func):
    """logging and saving logs."""
    global logs
    func(msg)
    logs.append(msg)

class CommandsHandler(SocketServer.BaseRequestHandler):
    '''class for handling commands from server upon receiving'''

    def handle(self):
        '''handle various commands'''
        data = self.request.recv(1024) 
        cmd = data.split()[0]
        if cmd == 'edit':
            self._update_config(*data.split()[1:])
        elif cmd == 'show':
            self._show_config()
    
    def _show_config(self):
        '''handle commands that show configs'''
        with open('config/node.json') as nodeConfigFile:
            nodeCfgs = json.load(nodeConfigFile)['node']
        data = ''.join('{0} = {1}\n'.format(key, nodeCfgs[key]) for key in
                nodeCfgs)
        self.request.send(data)
        print 'sent configs to ctlServer.'
 
    def _update_config(self, cfg, value):
        '''handle commands that update configs'''
        global intervalTime
        with open('config/node.json') as nodeConfigFile:
            nodeCfgs = json.load(nodeConfigFile)
        #TODO: Is there any better way to implement the following codes?
        if cfg == 'intervalTime':
            intervalTime = int(value)
            self.request.send(cfg + 'has been changed to' + value)
            nodeCfgs['node']['intervalTime'] = int(value)
            with open('config/node.json', 'w') as nodeCfgFile:
                json.dump(nodeCfgs, nodeCfgFile)
            print cfg + 'has been changed to' + value + 'by ctlServer.'

def recvCommands():
    '''receice commands from control server'''
    address = ('0.0.0.0', PORT)
    server = SocketServer.TCPServer(address, CommandsHandler)
    t = threading.Thread(target=server.serve_forever)
    t.setDaemon(True)
    t.start()

def nodeRun():
    with open("config/sensors.json") as sensorConfigFile:
        sensorCfgs = json.load(sensorConfigFile)['sensors']

    # Check the correctness of sensor config file and whether corresponding
    # plugins exist
    for sensorCfg in sensorCfgs:
        try:
            try:
                filename = sensorCfg['filename']
                enabled = sensorCfg['enabled']
                sensorname = sensorCfg['sensorname']
            except Exception:
                loggingSave("Missing option(s) in config file.", logging.error)
                raise
            loggingSave("Successfully load sensor {0} config file!".format(
                sensorname), logging.info)
        except Exception as e: # TODO: define exception for this
            loggingSave("Failed to load sensor config file! Please make sure" +
            " it's correct.", logging.error)
            raise e

    preTime = 0
    recvCommands()
    global intervalTime
    with open('config/node.json') as nodeConfigFile:
        nodeCfgs = json.load(nodeConfigFile)['node']
        intervalTime = nodeCfgs['intervalTime']
        nodeName = nodeCfgs['name']
        nodeID = nodeCfgs['node_id']
        if nodeID == 0:
            loggingSave("Not register at server yet. Please run register.py"
            " first.", logging.error)
            raise Exception("ERROR: Not register at server yet.")

    while True:
        curTime  = time.time()
        if preTime > curTime: # in case somehow current time in system is modified
            preTime = 0
        if (curTime - preTime) > intervalTime:
            preTime = curTime
            # Collect data form each sensor
            data = [{"name": nodeName, "node_id" : nodeID}]
            for sensorCfg in sensorCfgs:
                dataDict = {}
                sensorname = sensorCfg['sensorname']
                filename = sensorCfg['filename']
                enabled = sensorCfg['enabled']
                if enabled:
                    try:
                        # the following code works as long as fromlist is not empty
                        plugin = __import__('sensors.' + filename, fromlist=['a'])
                    except Exception:
                        loggingSave("Could not find sensor {0}'s plugin file!".format(
                            sensorname), logging.error)
                    dataDict = {}
                    try:
                        dataDict["value"] = plugin.getValue()
                        dataDict["unit"] = plugin.getUnit()
                        dataDict["value_name"] = plugin.getValueName()
                        dataDict["sensor"] = sensorname
                        dataDict["time"] = str(datetime.datetime.now())
                        data.append(dataDict)
                    except Exception:
                        loggingSave("Missing function(s) in {0}'s plugin file".format(
                            sensorname), logging.error)
            global logs
            loggingData = {"value_name": "log", "value": str(logs)}
            logs = []
            working = True
            output = "Time: " + str(datetime.datetime.now()) + '\n'
            for d in data:
                output = output + d['value_name'] + ':' + str(d['value']) + " " + d['unit']  
            print ""
            print "Time: " + str(datetime.datetime.now())
            for d in data:
                print d['value_name'] + ':' + str(d['value']) + " " + d['unit']  
                
            data.append("upload")
            upload.upload(json.dumps(data) + '\r\n\r\n')
            time.sleep(1)
if __name__ == '__main__':
    # ensures the main process doesn't terminate becasue of exceptions(neither
    # expected nor unexpected). Report the error message and let the 
    # server handle exceptions.
    import traceback
    import sys
    try:
        nodeRun()
    except Exception, e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        tb = traceback.format_exception(exc_type, exc_value, exc_tb)
        logging.CRITICAL(tb)
        data = [{"name": nodeName, "node_id" : nodeID}]
        data.append(tb)
        data.append("exception")
        upload.upload(data)
        nodeRun()
