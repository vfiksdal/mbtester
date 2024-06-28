##\package mbserver
# \brief CLI MODBUS servers
#
# Vegard Fiksdal (C) 2024
#
from mbtserver import *
from mbtclient import *

class ProxyObject():
    def __init__(self,server,client):
        self.server=server
        self.client=client
        self.lock=threading.Lock()
        self.override=True

        # Assign server callbacks
        self.server.di.addReadCallback(self.onServerRead)
        self.server.co.addReadCallback(self.onServerRead)
        self.server.hr.addReadCallback(self.onServerRead)
        self.server.ir.addReadCallback(self.onServerRead)
        self.server.di.addWriteCallback(self.onServerWrite)
        self.server.co.addWriteCallback(self.onServerWrite)
        self.server.hr.addWriteCallback(self.onServerWrite)
        self.server.ir.addWriteCallback(self.onServerWrite)

    def startProxy(self):
        # Connect client
        result=False
        if self.server.startServer():
            if self.client.connect():
                result=True
        return result

    def onServerWrite(self,datablock,address,value):
        retval=value
        if self.override:
            with self.lock:
                self.override=False
                logging.info('Writing profile['+datablock+']['+str(address)+']='+str(value))
                if not self.client.write(datablock,address,value,False):
                    retval=getattr(self.server,datablock).getValues(address)
                self.override=True
        return retval

    def onServerRead(self,datablock,address,value):
        retval=value
        if self.override:
            with self.lock:
                self.override=False
                logging.info('Reading profile['+datablock+']['+str(address)+']')
                read=self.client.read(datablock,address,False)
                if read!=None:
                    logging.info('Storing: profile['+datablock+']['+str(address)+']='+str(read))
                    getattr(self.server,datablock).setValues(address,read)
                    retval=read
                self.override=True
        return retval

if __name__ == "__main__":
    # Present options
    print(App.getAbout('proxy','CLI proxy for MODBUS Testing')+'\n')
    loader=Loader()
    print('Server options:')
    print(App.reportConfig(loader.serverargs))
    print('Client options:')
    print(App.reportConfig(loader.clientargs))

    # Run proxy
    server=ServerObject(loader.serverargs)
    client=ClientObject(loader.clientargs)
    proxy=ProxyObject(server,client)
    if proxy.startProxy():
        proxy.server.waitServer()
