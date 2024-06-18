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
import argparse,asyncio,logging,sys,threading,time

##\class AsyncServerObject
# \brief Asynchrous modbus server
class AsyncServerObject():
    ##\brief Initializes async server object
    # \param args Arguments to configure the object
    def __init__(self,args):
        # Parse profile and contexts
        self.profile=Utils.loadProfile(args.profile)
        self.di=DataBlock(self.profile['datablocks']['di'])
        self.co=DataBlock(self.profile['datablocks']['co'])
        self.hr=DataBlock(self.profile['datablocks']['hr'])
        self.ir=DataBlock(self.profile['datablocks']['ir'])
        self.slavecontext=ModbusSlaveContext(di=self.di, co=self.co, hr=self.hr, ir=self.ir)
        self.mastercontext=ModbusServerContext(slaves=self.slavecontext)
        self.identity=ModbusDeviceIdentification(info_name=self.profile['identity'])

        # Assign objects
        self.args=args
        self.server=None
        self.running=False

    ##\brief Starts the modbus server
    async def StartServer(self):
        self.running=True
        args=self.args
        if args.comm=='tcp':
            self.server = await StartAsyncTcpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer)
        if args.comm=='udp':
            self.server = await StartAsyncUdpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer,timeout=args.timeout)
        if args.comm=='serial':
            self.server = await StartAsyncSerialServer(context=self.mastercontext,identity=self.identity,port=args.port,baudrate=args.baudrate,bytesize=8,parity=args.parity,stopbits=1,framer=args.framer,timeout=args.timeout)
        self.running=False

    ##\brief Stops the modbus server
    async def StopServer(self):
        if self.running: await ServerAsyncStop()

##\class ServerObject
# \brief Threaded modbus server
class ServerObject(AsyncServerObject):
    ##\brief Initializes server object
    # \param args Arguments to configure the object
    def __init__(self,args):
        super().__init__(args)

    ##\brief Thread method to run the server
    def RunServer(self):
        self.running=True
        args=self.args
        if args.comm=='tcp':
            self.server = StartTcpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer)
        if args.comm=='udp':
            self.server = StartUdpServer(context=self.mastercontext,identity=self.identity,address=(args.host,args.port),framer=args.framer,timeout=args.timeout)
        if args.comm=='serial':
            self.server = StartSerialServer(context=self.mastercontext,identity=self.identity,port=args.port,baudrate=args.baudrate,bytesize=8,parity=args.parity,stopbits=1,framer=args.framer,timeout=args.timeout)
        self.running=False

    ##\brief Starts the modbus server in a background thread
    # \returns True if the server is running
    def StartServer(self):
        # Start server in background thread
        self.thread=threading.Thread(target=self.RunServer)
        self.thread.start()
        time.sleep(1)
        return self.running

    ##\brief Stops the modbus server
    def StopServer(self):
        if self.running:
            ServerStop()
            self.thread.join()


if __name__ == "__main__":
    # Parse command line options
    argformatter=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=54)
    parser=argparse.ArgumentParser(description='MBTester Client',formatter_class=argformatter)
    parser.add_argument('-c','--comm',choices=['tcp', 'udp', 'serial'],help='set communication, default is tcp',dest='comm',default='tcp',type=str)
    parser.add_argument('-f','--framer',choices=['ascii', 'rtu', 'socket'],help='set framer, default depends on --comm',dest='framer',default='socket',type=str)
    parser.add_argument('-l','--log',choices=['critical', 'error', 'warning', 'info', 'debug'],help='set log level, default is info',dest='log',default='info',type=str)
    parser.add_argument('-H','--host',help='set host, default is 127.0.0.1',dest='host',default='127.0.0.1',type=str)
    parser.add_argument('-P','--port',help='set tcp/udp/serial port',dest='port',default='502',type=str)
    parser.add_argument('-b','--baudrate',help='set serial device baud rate',dest='baudrate',default=9600,type=int)
    parser.add_argument('-x','--parity',choices=['O', 'E', 'N'],help='set serial device parity',dest='parity',default='N',type=str)
    parser.add_argument('-t','--timeout',help='set request timeout',dest='timeout',default=1,type=int)
    parser.add_argument('-p','--profile',help='modbus register profile to serve',dest='profile',default='',type=str)
    args = parser.parse_args()

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

    # Run async server
    server=AsyncServerObject(args)
    asyncio.run(server.StartServer())
