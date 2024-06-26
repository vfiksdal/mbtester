##\package mbtester
# \brief Simple loader mechanism for binary distributions
#
# Vegard Fiksdal (C) 2024
#
#from mbtclient import *
#from mbtserver import *
from mbtproxy import *

# Use parent parser to get --client and --server option in the parser
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('-C','--client',help='Run as MODBUS client',dest='client',action='store_true')
parser.add_argument('-S','--server',help='Run as MODBUS server',dest='server',action='store_true')

# Split arguments in client- and server arguments
cargs=[]
sargs=[]
client,server=False,False
for i in range(1,len(sys.argv)):
    aclient=sys.argv[i]=='--client' or sys.argv[i]=='-C'
    aserver=sys.argv[i]=='--server' or sys.argv[i]=='-S'
    if aclient:     client,server=True,False
    elif aserver:   client,server=False,True
    elif client:    cargs.append(sys.argv[i])
    elif server:    sargs.append(sys.argv[i])
    else:
        cargs.append(sys.argv[i])
        sargs.append(sys.argv[i])

# Check client- server options
usage='%(prog)s --client|--server [options]'
aclient='--client' in sys.argv or '-C' in sys.argv
aserver='--server' in sys.argv or '-S' in sys.argv
ahelp='--help' in sys.argv or '-h' in sys.argv

# Load appropriate code
print(App.getAbout()+'\n')
server=None
if aserver and aclient:
    sargs=App.parseArguments(args=sargs,parents=[parser],usage=usage,offset=0)
    cargs=App.parseArguments(args=cargs,parents=[parser],usage=usage,offset=-1)
    proxy=RunProxy(sargs,cargs)
    if proxy: server=proxy.server
elif aserver:
    args=App.parseArguments(args=sargs,parents=[parser],usage=usage,offset=0)
    server=RunServer(args)
elif aclient:
    args=App.parseArguments(args=cargs,parents=[parser],usage=usage,offset=-1)
    RunClient(args)
elif ahelp:
    App.parseArguments(args=sargs,parents=[parser],usage=usage,offset=-1)
else:
    print('Please specify --client or --server')

# Wait for server to terminate
if server:
    try:
        while server.running:
            time.sleep(0.5)
    except:
        server.stopServer()
