##\package mbserver
# \brief CLI MODBUS servers
#
# Vegard Fiksdal (C) 2024
#
from pymodbus import pymodbus_apply_logging_config
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
import asyncio,logging,sys,threading,time

##\class AsyncServerObject
# \brief Asynchrous modbus server
class AsyncServerObject():
    ##\brief Initializes async server object
    # \param args Arguments to configure the object
    def __init__(self,args):
        # Parse profile and contexts
        self.profile=Utils.loadProfile(args.profile)
        self.di=DataBlock(self.profile,'di')
        self.co=DataBlock(self.profile,'co')
        self.hr=DataBlock(self.profile,'hr')
        self.ir=DataBlock(self.profile,'ir')
        self.slavecontext=ModbusSlaveContext(di=self.di, co=self.co, hr=self.hr, ir=self.ir)
        if args.slaveid:
            self.mastercontext=ModbusServerContext(slaves={args.slaveid:self.slavecontext},single=False)
        else:
            self.mastercontext=ModbusServerContext(slaves=self.slavecontext,single=True)
        self.identity=ModbusDeviceIdentification(info_name=self.profile['identity'])

        # Assign objects
        self.args=args
        self.server=None
        self.running=False

    ##\brief Starts the modbus server
    async def startServer(self):
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


if __name__ == "__main__":
    # Parse command line options
    aboutstring=Utils.getAppName()+' Server '+Utils.getAppVersion()+'\n'
    aboutstring+='Server for MODBUS Testing\n'
    aboutstring+='Vegard Fiksdal(C)2024'
    args = Utils.parseArguments(aboutstring)

    # Check for profile
    if len(args.profile)==0:
        print('Please set a profile to use (See -p or --profile parameter)')
        sys.exit()
    elif not os.path.exists(args.profile):
        print('Profile file '+args.profile+' does not exist')
        sys.exit()

    # Enable logging
    args.log=args.log.upper()
    level=logging._nameToLevel[args.log]
    logging.basicConfig(level=level,stream=sys.stdout,format='%(asctime)s %(levelname)s\t%(message)s')
    pymodbus_apply_logging_config(args.log)
    debug = (args.log=='DEBUG')

    # Present options
    print(aboutstring+'\n')
    print(Utils.reportConfig(args))

    # Run async server
    server=AsyncServerObject(args)
    asyncio.run(server.startServer())
