##\package mbtester
# \brief Simple loader mechanism for binary distributions
#
# Vegard Fiksdal (C) 2024
#
#from mbtclient import *
#from mbtserver import *
from mbtproxy import *

# Load appropriate code
print(App.getAbout()+'\n')
loader=Loader()
if loader.flags.server and loader.flags.client:
    print('Server options:')
    print(App.reportConfig(loader.serverargs))
    print('Client options:')
    print(App.reportConfig(loader.clientargs))
    server=ServerObject(loader.serverargs)
    client=ClientObject(loader.clientargs)
    proxy=ProxyObject(server,client)
    if proxy.startProxy():
        proxy.server.waitServer()
elif loader.flags.server:
    print(App.reportConfig(loader.serverargs))
    server=ServerObject(loader.serverargs)
    if server.startServer():
        server.waitServer()
elif loader.flags.client:
    print(App.reportConfig(loader.clientargs))
    client=ClientObject(loader.clientargs)
    if client.connect():
        output=client.download()
        output=json.dumps(output,indent=4)
        print(str(output))
        client.close()
else:
    print('Please specify --client or --server')

