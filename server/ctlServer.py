"""
Control server of PiSensorNetwork. 
It is able to send requsts to nodes
from command line.
"""

import ctlCommands

def discription():
    """
    Print the discription of this command-line tool on the screen.
    """

    text = "CTL_SERVER: an ez tool to control node of sensor network.\n"
    print text
    cmds = [getattr(ctlCommands, attr) for attr in dir(ctlCommands) 
            if not attr.startswith('_')]
    for cmd in cmds:
        print cmd.__doc__

def main():
    discription();

    while True:
        request = raw_input('cmd > ').split()
        cmd = request[0]
        if hasattr(ctlCommands, cmd):
            cmdInst = getattr(ctlCommands, cmd)
            msg = cmdInst(*request)
            print msg
        else:
            print 'Command Wrong! Check and type again.'
            continue
            
        

main()

'''if __name__ == '__main__':
    retry_cnt = 0;
    while True:
        try:
            main()
        except socket.error as e:
            print e
            print 'Socket Error! Retry for' + retry_cnt + 'times'
            continue
        except Exception as e_unhandle:
            print e_unhandle
            break'''


