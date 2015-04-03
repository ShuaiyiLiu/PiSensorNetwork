import datetime
import json
import string
import time
import os

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
intervalTime = 5 # TODO: set a reasonable inital and can be changed by server
while True:
    curTime  = time.time()
    if preTime > curTime: # in case somehow current time in system is modified
        preTime = 0
    if (curTime - preTime) > intervalTime:
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
                    data.append(dataDict)
                except Exception:
                    print "Missing function(s) in {0}'s plugin file".format(
                          sensorname)
        working = True
        print ""
        print "Time: " + str(datetime.datetime.now())
        for d in data:
            print d['value_name'] + ':' + str(d['value']) + " " + d['unit']
        time.sleep(1)













