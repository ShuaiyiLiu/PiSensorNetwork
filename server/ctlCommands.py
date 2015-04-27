"""
Implementation of commands in control server.
"""

def show_nodes(*args):
    '''show_nodes: list all avaliable nodes.'''
    pass

def show_configs(*args):
    '''show_configs <node-ip-1> <node-ip-2> ...: list current node config'.
    '''
    pass

def edit_configs(*args):
    '''edit_configs <node-ip> <config-name> <value>: change config value
    for node(s)
    '''
    if len(args) != 4:
        print args
        return 'Invalid arguments. Please check again.'

    _, ip, cfgName, value = args
    # TODO: Check if ip is valid
    port = 9999 # TODO: FIXTHIS. ADD TO CONFIG
    import socket
    
    retryCnt = 3 # Times of retry for each command
    while retryCnt >= 0:
        retryCnt -= 1
        print str(retryCnt) + 'times of retry left.'
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            print 'try to connect to {0}:{1}'.format(ip, port)
            sock.connect((ip, port))
            sock.sendall(cfgName + ' ' + value)
        except socket.error as e:
            print 'Error: socket error.', e
    def recv_all(sock):
        more = sock.recv(1024)
        data = ''
        while len(more):
            print more
            data += more
            more = sock.recv(1024)
        return data
    return recv_all(sock)



