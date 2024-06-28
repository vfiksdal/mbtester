##\package qmbtester
# \brief Simple loader mechanism for binary distributions
#
# Vegard Fiksdal (C) 2024
#
from qmbtclient import *
from qmbtserver import *
from qmbtproxy import *

# Load appropriate code
loader=Loader(gui=True)
app=QApplication(sys.argv)
if loader.flags.server and loader.flags.client:
    aboutstring=App.getAbout('server','GUI proxy for MODBUS Testing')
    window=ProxyUI(loader.serverargs,loader.clientargs,aboutstring)
elif loader.flags.client:
    aboutstring=App.getAbout('client','GUI client for MODBUS Testing')
    window=ClientUI(loader.clientargs,aboutstring)
else:
    aboutstring=App.getAbout('server','GUI server for MODBUS Testing')
    window=ServerUI(loader.serverargs,aboutstring)

# Run application
app.exec()
