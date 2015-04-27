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

PORT = 9999 # TODO: config
intervalTime = 5 # TODO : config

class CommandsHandler(SocketServer.BaseRequestHandler):
    '''handle commands from server upon receiving'''

    def handle(self):
        global intervalTime
        data = self.request.recv(1024) # TODO: use recv_all and sendall
        
        cfg, value = data.split()
        
        # TODO: edit all cfgs avaliable
        if cfg == 'intervalTime' and value.isdigit():
            intervalTime = int(value)
            print intervalTime
            self.request.send(cfg + 'has been changed to' + value)


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
                print "Missing option(s) in config file."
                raise
            print "Successfully load sensor {0} config file!".format(sensorname)
        except Exception as e: # TODO: define exception for this
            print "Failed to load sensor config file! Please make sure it's correct."
            raise e

    preTime = 0
    recvCommands()
    while True:
        curTime  = time.time()
        if preTime > curTime: # in case somehow current time in system is modified
            preTime = 0
        if (curTime - preTime) > intervalTime:
            print intervalTime
            preTime = curTime
            # Collect data form each sensor
            data = []
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
                        print "Could not find sensor {0}'s plugin file!".format(
                            sensorname)
                    dataDict = {}
                    try:
                        dataDict["value"] = plugin.getValue()
                        dataDict["unit"] = plugin.getUnit()
                        dataDict["value_name"] = plugin.getValueName()
                        dataDict["sensor"] = sensorname
                        dataDict["time"] = str(datetime.datetime.now())
                        data.append(dataDict)
                    except Exception:
                        print "Missing function(s) in {0}'s plugin file".format(
                            sensorname)
            working = True
            output = "Time: " + str(datetime.datetime.now()) + '\n'
            for d in data:
                output = output + d['value_name'] + ':' + str(d['value']) + " " + d['unit']  
            print ""
            print "Time: " + str(datetime.datetime.now())
            for d in data:
                print d['value_name'] + ':' + str(d['value']) + " " + d['unit']  
                
            upload.upload(json.dumps(data) + '\r\n\r\n')
            time.sleep(1)
nodeRun()
'''
if __name__ == '__main__':
    # ensures the main process doesn't terminate becasue of exceptions(neither
    # expected nor unexpected). Report the error message and let the 
    # server handle exceptions.
    while True:
        try:
            nodeRun()
        except Exception as e:
            print e
            upload.upload
'''












