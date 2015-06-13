#! /usr/bin/env python
'''
This module check local database and upload data missing from server, and also
defines function that dumps data into local database.
'''

import socket
import json
import datetime
import sys
import time
import logging

MAX_LENGTH = 1024
DEFAULT_TEMPERATURE = 20
DEFAULT_HUMIDITY = 1
logging.basicConfig(format='%(asctime)s <%(levelname)s> %(message)s', level=logging.DEBUG)

def _connectServer():
    with open("config/node.json") as nodeConfigFile:
        serverConfig = json.load(nodeConfigFile)['server']
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    # TODO: supporting argument selecting host and port
    host = serverConfig['host']
    port = serverConfig['port']
    sock.connect((host, port))
    curTime = str(datetime.datetime.now())[0:-7]
    sys.stdout.flush()
    return sock

def upload(data):
    try:
        sock = _connectServer()
        sock.sendall(data)
        more = sock.recv(MAX_LENGTH)
        data = ''
        while len(more):
            data += more
            more = sock.recv(MAX_LENGTH)
        return data
    except socket.error as e:
        logging.warn('cannot send data to server.')
        raise e

def dbDump(data):
    """Function that dumps data to local database. """
    import MySQLdb
    from contextlib import closing
    with open("config/node.json") as nodeCfgFile:
        dbCfg = json.load(nodeCfgFile)["database"]
        db = MySQLdb.connect(db = dbCfg["db"], user = dbCfg["user"], passwd =
                dbCfg["passwd"])
        max_rows = dbCfg["max_rows"]
    temperature = DEFAULT_TEMPERATURE
    humidity = DEFAULT_HUMIDITY
    with closing(db.cursor()) as cur:
        for d in data[1:]:
            value = d["value"]
            value_name = d["value_name"]
            if d.has_key("time"):
                creat_time = d["time"]
            if value_name == "Temperature":
                temperature = value
            elif value_name == "Humidity":
                humidity = value
        cur.execute("""INSERT INTO map_data (temperature, humidity,
                creat_time) VALUES (%s, %s, %s)""",
                (temperature, humidity, creat_time))
        db.commit()
    db.close()

def dbDataAfterDate(date):
    """Return list of all columns with creat_time larger than date."""
    import MySQLdb
    from contextlib import closing
    with open("config/node.json") as nodeCfgFile:
        dbCfg = json.load(nodeCfgFile)["database"]
        db = MySQLdb.connect(db = dbCfg["db"], user = dbCfg["user"], passwd =
                dbCfg["passwd"])
    
    with closing(db.cursor()) as cur:
        cur.execute("SELECT * FROM map_data WHERE creat_time > %s", (date,))
        rawDatas = cur.fetchall()
        if len(rawDatas) == 0:
            return None
        colDesc = ["value", "value_name", "time"]
        f = lambda x, y: x + [dict(zip(colDesc, [y[0], "Temperature", str(y[2])])),
                              dict(zip(colDesc, [y[1], "Humidity", str(y[2])])), 
                              {"value": 0, "value_name": "DataID"}]
        newDatas = reduce(f, rawDatas, [])
        return newDatas
    db.close() 


def main():
    preTime = 0
    lstKnwn = False
    while True:
        # get upload interval from config file. 
        with open("config/node.json") as nodeCfgFile:
            nodeCfg = json.load(nodeCfgFile)["node"]
        intervalTime = nodeCfg["intervalTime"]
        # upload if interval time is up
        curTime  = time.time()
        if preTime > curTime: # in case somehow current time in system is modified
            preTime = 0
        if (curTime - preTime) > intervalTime:
            preTime = curTime 
            # send upload_request message to server and receive datatime if
            # necessary
            if not lstKnwn:
                request = [{"node_id": nodeCfg["node_id"]}, "upload_request"]
                recvData = upload(json.dumps(request) + "\r\n\r\n")
                rcvds = recvData.split()
                dateStr = rcvds[-2] + ' ' + rcvds[-1]
                if dateStr.find('.') >= 0:
                    rcvDate = datetime.datetime.strptime(dateStr, "%Y-%m-%d %X.%f")
                else:
                    rcvDate = datetime.datetime.strptime(dateStr, "%Y-%m-%d %X")
                newData = dbDataAfterDate(rcvDate)
            # TODO: update lstKnwn 
            if newData is not None:
                upload_data = [{"node_id": nodeCfg["node_id"]}]
                upload_data.extend(newData)
                upload_data.append("upload")
                print upload_data
                upload(json.dumps(upload_data) + "\r\n\r\n")
        time.sleep(intervalTime / 10)

if __name__ == "__main__":
    main()
