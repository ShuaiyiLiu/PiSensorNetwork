"""
Implementation of commands in control server.
"""

_INVALID_ARGS = 'Invalid arguments! Please check again!'
_CONFIG_FILE = 'server.json'

def show_nodes(*args):
    '''show_nodes: list all avaliable nodes.'''
    import MySQLdb
    import json
    from contextlib import closing
    with open("server.json") as serverCfgFile:
        dbCfg = json.load(serverCfgFile)["database"]
        db = MySQLdb.connect(db = dbCfg["db"], user = dbCfg["user"])
    with closing(db.cursor()) as cur:
        cur.execute("""SELECT * FROM map_node;""")
        nodes = cur.fetchall()
        for node in nodes:
            if node is not None:
                print "Node ID: {}      Node name: {}        Node IP: {}".format(*node)
    db.close()

def _get_port():
    '''get port that control service is used from config file'''
    import json
    with open(_CONFIG_FILE) as serverConfigFile:
        ctlConfig = json.load(serverConfigFile)['ctlServer']
    port = ctlConfig['port']
    return port

def _recv_all(sock):
    more = sock.recv(1024)
    data = ''
    while len(more):
        data += more
        more = sock.recv(1024)
    return data

def show_configs(*args):
    '''show_configs <node-ip-1> <node-ip-2> ...: list current node config'.
    '''
    import socket 
    port = _get_port()
    configs = '' 
    args = args[1:]
    for addr in args: 
        retryCnt = 3
        while retryCnt >= 0:
            retryCnt -= 1
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((addr, port))
                sock.sendall('show')
                break
            except socket.error as e:
                pass # if it's socket error, retry. 
        configs = '[{0}]\n{1}'.format(addr, _recv_all(sock)) 
    return configs

def edit_configs(*args):
    '''edit_configs <node-ip> <config-name> <value>: change config value
    for node(s)
    '''
    if len(args) != 4:
        return _INVALID_ARGS 
    # TODO: Check if ip is valid
    import socket
    port = _get_port() 
    _, ip, cfgName, value = args
    retryCnt = 3 # Times of retry for each command
    while retryCnt >= 0:
        retryCnt -= 1
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.sendall('edit ' + cfgName + ' ' + value)
            break
        except socket.error as e:
            pass # if it's socket error, retry. 
    return _recv_all(sock)



