##\package mbserver
# \brief CLI MODBUS servers
#
# Vegard Fiksdal (C) 2024
#
from mbtserver import *
from mbtclient import *

class ProxyObject():
    def __init__(self,serverargs,clientargs):
        self.serverargs=serverargs
        self.clientargs=clientargs
        self.server=ServerObject(serverargs)
        self.client=ClientObject(clientargs)
        self.lock=threading.Lock()
        self.override=True

    def startProxy(self):
        # Assign server callbacks
        self.server.di.addReadCallback(self.onServerRead)
        self.server.co.addReadCallback(self.onServerRead)
        self.server.hr.addReadCallback(self.onServerRead)
        self.server.ir.addReadCallback(self.onServerRead)
        self.server.di.addWriteCallback(self.onServerWrite)
        self.server.co.addWriteCallback(self.onServerWrite)
        self.server.hr.addWriteCallback(self.onServerWrite)
        self.server.ir.addWriteCallback(self.onServerWrite)

        # Connect client
        result=False
        if self.client.connect():
            if self.server.startServer():
                result=True
        return result

    def onServerWrite(self,datablock,address,value):
        retval=value
        if self.override:
            with self.lock:
                self.override=False
                if not self.client.write(datablock,address,value):
                    retval=getattr(self.server,datablock).getValues(address)
                self.override=True
        return retval

    def onServerRead(self,datablock,address,value):
        retval=value
        if self.override:
            with self.lock:
                self.override=False
                read=self.client.read(datablock,address)
                if read!=None:
                    getattr(self.server,datablock).setValues(address,read)
                    retval=read
                self.override=True
        return retval

def RunProxy(serverargs,clientargs):
    # Check for profile
    if len(clientargs.profile): profile=clientargs.profile
    if len(serverargs.profile): profile=serverargs.profile
    serverargs.profile=profile
    clientargs.profile=profile
    if len(profile)==0:
        print('Please set a profile to use (See -p or --profile parameter)')
        sys.exit()
    elif not Profiles.getProfile(serverargs,profile):
        print('Profile file '+args.profile+' not found')
        sys.exit()

    # Enable logging
    level=logging._nameToLevel[serverargs.log.upper()]
    if level<logging._nameToLevel[clientargs.log.upper()]:
        level=logging._nameToLevel[clientargs.log.upper()]
    serverargs.log=logging._levelToName[level]
    clientargs.log=logging._levelToName[level]
    logging.basicConfig(level=level,stream=sys.stdout,format='%(asctime)s %(levelname)s\t%(message)s')
    pymodbus_apply_logging_config(serverargs.log)

    # Present options
    print('Server options:')
    print(App.reportConfig(serverargs))
    print('Client options:')
    print(App.reportConfig(clientargs))

    # Run proxy
    proxy=ProxyObject(serverargs,clientargs)
    if proxy.startProxy():
        return proxy
    else:
        return None

if __name__ == "__main__":
    # Parse command line options
    aboutstring=App.getAbout('server','CLI server for MODBUS Testing')
    print(aboutstring+'\n')
    args = App.parseArguments(offset=0)

    # Run server
    RunServer(args)
