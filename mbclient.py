##\package mbclient
# \brief CLI MODBUS client
#
# Vegard Fiksdal (C) 2024
#
from pymodbus import pymodbus_apply_logging_config
import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    ModbusException,
)
import argparse,logging,sys
from common import *

##\class AsyncClientObject
# \brief Asyncronous client object
class AsyncClientObject():
    ##\brief Initializes object
    # \param Parsed commandline arguments
    async def __init__(self,args):
        # Parse profiles
        self.profile=Utils.loadProfile(args.profile)
        self.slaveid=args.slaveid
        self.offset=args.offset

        # Load client object
        self.args=args
        self.client=None
        if args.comm=='tcp':
            self.client = ModbusClient.AsyncModbusTcpClient(args.host,port=args.port,framer=args.framer,timeout=args.timeout,retries=3)
        if args.comm=='udp':
            self.client = ModbusClient.AsyncModbusUdpClient(args.host,port=args.port,framer=args.framer,timeout=args.timeout,retries=3)
        if args.comm=='serial':
            self.client = ModbusClient.AsyncModbusSerialClient(args.port,framer=args.framer,baudrate=args.baudrate,parity=args.parity,timeout=args.timeout,strict=True,bytesize=8,stopbits=1,retries=3,handle_local_echo=False)

    ##\brief Connect to the server
    # \return True if succsessfully connected
    async def Connect(self):
        if self.client:
            await client.connect()
            if not client.connected: client=None
        return (self.client!=None)

    ##\brief Read registers from the server
    # \param datablock Datablock to read from (di,co,hr or ir)
    # \param address Register address to read from
    # \return Decoded value, or None upon failure
    async def Read(self,datablock,address):
        response=None
        try:
            # Parse register information
            registerdata=self.profile['datablocks'][datablock][address]
            registeraddress=int(address)+self.offset
            count=Utils.registersPerValue(registerdata)

            # Execute request
            if datablock=='di': response = await self.client.read_discrete_inputs(registeraddress,count,self.slaveid)
            if datablock=='co': response = await self.client.read_coils(registeraddress,count,self.slaveid)
            if datablock=='hr': response = await self.client.read_holding_registers(registeraddress,count,self.slaveid)
            if datablock=='ir': response = await self.client.read_input_registers(registeraddress,count,self.slaveid)
        except ModbusException as exc:
            logging.error('ModbusException: '+str(exc))
            return None
        if response.isError() or isinstance(response, ExceptionResponse):
            logging.warning(str(response))
            return None
        return Utils.decodeRegister(registerdata,response.registers)

    ##\brief Write registers to the server
    # \param datablock Datablock to write to (di,co,hr or ir)
    # \param address Register address to write to
    # \return True upon success
    async def Write(self,datablock,address,value):
        response=None
        try:
            # Parse register information
            registerdata=self.profile['datablocks'][datablock][address]
            registeraddress=int(address)+self.offset
            values=Utils.encodeRegister(registerdata,value)

            # Execute request
            if datablock=='di': pass
            if datablock=='co': response = await self.client.write_coil(registeraddress,value,self.slaveid)
            if datablock=='hr': response = await self.client.write_registers(registeraddress,values,self.slaveid)
            if datablock=='ir': pass
        except ModbusException as exc:
            logging.error('ModbusException: '+str(exc))
            return None
        if response.isError() or isinstance(response, ExceptionResponse):
            logging.warning(str(response))
            return None
        return True

    ##\brief Read all registers from the server
    # \return dictionary of all read values
    async def Download(self):
        output={}
        output['identity']=self.profile['identity']
        output['datablocks']={}
        for datablock in self.profile['datablocks']:
            for address in self.profile['datablocks'][datablock]:
                value=await self.Read(datablock,address)
                if value:
                    if not datablock in output['datablocks']: output['datablocks'][datablock]={}
                    output['datablocks'][datablock][address]={}
                    output['datablocks'][datablock][address]['name']=self.profile['datablocks'][datablock][address]['dsc']
                    output['datablocks'][datablock][address]['value']=value
        return output

    ##\brief Close connection to server
    def Close(self):
        if self.client: self.client.close()

##\class ClientObject
# \brief Syncronous client object
class ClientObject():
    ##\brief Initializes object
    # \param Parsed commandline arguments
    def __init__(self,args):
        # Parse profiles
        self.profile=Utils.loadProfile(args.profile)
        self.slaveid=args.slaveid
        self.offset=args.offset

        # Load client object
        self.args=args
        self.client=None
        if args.comm=='tcp':
            self.client = ModbusClient.ModbusTcpClient(args.host,port=args.port,framer=args.framer,timeout=args.timeout,retries=3)
        if args.comm=='udp':
            self.client = ModbusClient.ModbusUdpClient(args.host,port=args.port,framer=args.framer,timeout=args.timeout,retries=3)
        if args.comm=='serial':
            self.client = ModbusClient.ModbusSerialClient(args.port,framer=args.framer,baudrate=args.baudrate,parity=args.parity,timeout=args.timeout,strict=True,bytesize=8,stopbits=1,retries=3,handle_local_echo=False)

    ##\brief Connect to the server
    # \return True if succsessfully connected
    def Connect(self):
        if self.client:
            self.client.connect()
            if not self.client.connected: self.client=None
        return (self.client!=None)

    ##\brief Read registers from the server
    # \param datablock Datablock to read from (di,co,hr or ir)
    # \param address Register address to read from
    # \return Decoded value, or None upon failure
    def Read(self,datablock,address):
        response=None
        try:
            # Parse register information
            registerdata=self.profile['datablocks'][datablock][address]
            registeraddress=int(address)+self.offset
            count=Utils.registersPerValue(registerdata)

            # Execute request
            if datablock=='di': response = self.client.read_discrete_inputs(registeraddress,count,self.slaveid)
            if datablock=='co': response = self.client.read_coils(registeraddress,count,self.slaveid)
            if datablock=='hr': response = self.client.read_holding_registers(registeraddress,count,self.slaveid)
            if datablock=='ir': response = self.client.read_input_registers(registeraddress,count,self.slaveid)
        except ModbusException as exc:
            logging.error('ModbusException: '+str(exc))
            return None
        if response.isError() or isinstance(response, ExceptionResponse):
            logging.warning(str(response))
            return None
        return Utils.decodeRegister(registerdata,response.registers)

    ##\brief Write registers to the server
    # \param datablock Datablock to write to (di,co,hr or ir)
    # \param address Register address to write to
    # \return True upon success
    def Write(self,datablock,address,value):
        response=None
        try:
            # Parse register information
            registerdata=self.profile['datablocks'][datablock][address]
            registeraddress=int(address)+self.offset
            values=Utils.encodeRegister(registerdata,value)

            # Execute request
            if datablock=='di': pass
            if datablock=='co': response = self.client.write_coil(registeraddress,value,self.slaveid)
            if datablock=='hr': response = self.client.write_registers(registeraddress,values,self.slaveid)
            if datablock=='ir': pass
        except ModbusException as exc:
            logging.error('ModbusException: '+str(exc))
            return None
        if response.isError() or isinstance(response, ExceptionResponse):
            logging.warning(str(response))
            return None
        return True

    ##\brief Read all registers from the server
    # \return dictionary of all read values
    def Download(self):
        output={}
        output['identity']=self.profile['identity']
        output['datablocks']={}
        for datablock in self.profile['datablocks']:
            for address in self.profile['datablocks'][datablock]:
                value=self.Read(datablock,address)
                if value:
                    if not datablock in output['datablocks']: output['datablocks'][datablock]={}
                    output['datablocks'][datablock][address]={}
                    output['datablocks'][datablock][address]['name']=self.profile['datablocks'][datablock][address]['dsc']
                    output['datablocks'][datablock][address]['value']=value
        return output

    ##\brief Close connection to server
    def Close(self):
        if self.client: self.client.close()


if __name__ == "__main__":
    # Parse command line options
    argformatter=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=54)
    parser=argparse.ArgumentParser(description='MBTester Client',formatter_class=argformatter)
    parser.add_argument('-c','--comm',choices=['tcp', 'udp', 'serial'],help='set communication, default is tcp',dest='comm',default='tcp',type=str)
    parser.add_argument('-f','--framer',choices=['ascii', 'rtu', 'socket'],help='set framer, default depends on --comm',dest='framer',default='socket',type=str)
    parser.add_argument('-s','--slaveid',help='set slave id',dest='slaveid',default=1,type=int)
    parser.add_argument('-o','--offset',help='address offset',dest='offset',default=-1,type=int)
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
    logging.basicConfig(level=logging.INFO,stream=sys.stdout,format='%(asctime)s - %(levelname)s - %(message)s')
    pymodbus_apply_logging_config(args.log.upper())
    debug = (args.log.upper()=='DEBUG')

    # Download client data
    client=ClientObject(args)
    output=client.Download()
    client.Close()

    # Print result
    output=json.dumps(output,indent=4)
    print(str(output))

