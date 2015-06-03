#! /usr/bin/env python
'''
This module defines functions that upload data and errors from nodes to server.
'''
import socket
import json
import datetime
import sys

MAX_LENGTH = 1024

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
    except socket.error:
        print 'cannot send data to server.'
        pass

def dbDump(data):
    import MySQLdb
    from contextlib import closing
    with open("config/node.json") as nodeCfgFile:
        dbCfg = json.load(serverCfgFile)["database"]
        db = MySQLdb.connect(db = dbCfg["db"], user = dbCfg["user"])
        max_rows = dbCfg["max_rows"]
    temperature = 20
    humidity = 5
    with closing(db.cursor()) as cur:
        cur.execute("""SELECT data_id, MAX(collect_time) as 
                max_collect_time FROM map_data
                GROUP BY data_id""")
        row = cur.fetchone()
        data_id = row[0]
        for d in data[1:]:
            value = d["value"]
            value_name = d["value_name"]
            if d.has_key("time"):
                collect_time = d["time"]
            if value_name == "Temperature":
                temperature = value
            elif value_name == "Humidity":
                humidity = value

        cur.execute("""INSERT INTO map_data (temperature, humidity,
                collect_time, data_id) VALUES (%s, %s, %s, %s) ON 
                DUPLICATE KEY UPDATE 
                temperature = VALUES(temperature),
                humidity = VALUES(humidity),
                collect_time = VALUES(collect_time),
                data_id = VALUES(data_id)""", 
                (temperature, humidity, collect_time, (data_id + 1) % 
                max_rows))
    db.close()

def main():
    pass

if __name__ == "__main__":
    main()
