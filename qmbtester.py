##\package qmbtester
# \brief Simple loader mechanism for binary distributions
#
# Vegard Fiksdal (C) 2024
#
from qmbtclient import *
from qmbtserver import *

# Load appropriate code
aboutstring=App.getAbout('server')
print(App.getAbout()+'\n')
loader=Loader(gui=True)
if loader.flags.server and loader.flags.client:
    print('Proxy not yet supported')
elif loader.flags.client:
    RunClient(loader.clientargs,aboutstring)
else:
    RunServer(loader.serverargs,aboutstring)
