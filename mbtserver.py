##\package mbtserver
# \brief CLI MODBUS servers
#
# Vegard Fiksdal (C) 2024
#
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import (
    ModbusServerContext,
    ModbusSlaveContext
)
from pymodbus.server import (
    StartAsyncSerialServer,
    StartAsyncTcpServer,
    StartAsyncUdpServer,
    StartSerialServer,
    StartTcpServer,
    StartUdpServer,
    ServerAsyncStop,
    ServerStop
)
from common import *
import threading,time

##\class AsyncServerObject
# \brief Asynchrous modbus server
class AsyncServerObject():
    ##\brief Initializes async server object
    # \param args Arguments to configure the object
    def __init__(self,args):
        # Parse profile and contexts
        self.profile=Profiles.loadProfile(args,args.profile)
        self.di=DataBlock(self.profile,'di',args.strict)
        self.co=DataBlock(self.profile,'co',args.strict)
        self.hr=DataBlock(self.profile,'hr',args.strict)
        self.ir=DataBlock(self.profile,'ir',args.strict)
        self.slavecontext=ModbusSlaveContext(di=self.di, co=self.co, hr=self.hr, ir=self.ir)
        if args.deviceid:
            self.mastercontext=ModbusServerContext(slaves={args.deviceid:self.slavecontext},single=False)
        else:
            self.mastercontext=ModbusServerContext(slaves=self.slavecontext,single=True)
        self.identity=ModbusDeviceIdentification(info_name=self.profile['identity'])

        # Assign objects
        self.args=args
        self.server=None
        self.running=False

    ##\brief Starts the modbus server
    async def startServer(self):
        # Check if socket is available
        if self.args.comm=='tcp' or self.args.comm=='udp':
            if not Utilities.checkSocket(self.args.host,int(self.args.port)):
                logging.critical('Could not bind to network interface: '+str(self.args.host)+':'+str(self.args.port))
                return False

        # Start server
        self.running=True
        args=self.args
        if args.comm=='tcp':    self.server = await StartAsyncTcpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer)
        if args.comm=='udp':    self.server = await StartAsyncUdpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer,timeout=args.timeout)
        if args.comm=='serial': self.server = await StartAsyncSerialServer(context=self.mastercontext,identity=self.identity,port=args.serial,baudrate=args.baudrate,bytesize=args.bytesize,parity=args.parity,stopbits=1,framer=args.framer,timeout=args.timeout)
        self.running=False

    ##\brief Stops the modbus server
    async def stopServer(self):
        if self.running: await ServerAsyncStop()

##\class ServerObject
# \brief Threaded modbus server
class ServerObject(AsyncServerObject):
    ##\brief Initializes server object
    # \param args Arguments to configure the object
    def __init__(self,args):
        super().__init__(args)

    ##\brief Thread method to run the server
    def runServer(self):
        self.running=True
        args=self.args
        if args.comm=='tcp':    self.server = StartTcpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer)
        if args.comm=='udp':    self.server = StartUdpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer,timeout=args.timeout)
        if args.comm=='serial': self.server = StartSerialServer(context=self.mastercontext,identity=self.identity,port=args.serial,baudrate=args.baudrate,bytesize=args.bytesize,parity=args.parity,stopbits=1,framer=args.framer,timeout=args.timeout)
        self.running=False

    ##\brief Starts the modbus server in a background thread
    # \returns True if the server is running
    def startServer(self):
        # Check if socket is available
        if self.args.comm=='tcp' or self.args.comm=='udp':
            if not Utilities.checkSocket(self.args.host,int(self.args.port)):
                logging.critical('Could not bind to network interface: '+str(self.args.host)+':'+str(self.args.port))
                return False

        # Start server in background thread
        self.thread=threading.Thread(target=self.runServer)
        self.thread.start()
        time.sleep(1)
        return self.running

    ##\brief Stops the modbus server
    def stopServer(self):
        if self.running:
            ServerStop()
            self.thread.join()

    ##\brief Wait for server to terminate
    def waitServer(self):
        try:
            while self.running:
                time.sleep(0.5)
        except:
            self.stopServer()

if __name__ == "__main__":
    # Parse command line options
    print(App.getAbout('server','CLI server for MODBUS Testing')+'\n')
    serverargs=Loader().serverargs
    print(App.reportConfig(serverargs))
    server=ServerObject(serverargs)
    if server.startServer():
        server.waitServer()
