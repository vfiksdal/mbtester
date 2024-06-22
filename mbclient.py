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
import logging,sys,threading,time
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
            self.client = ModbusClient.AsyncModbusSerialClient(args.serial,framer=args.framer,baudrate=args.baudrate,parity=args.parity,timeout=args.timeout,strict=True,bytesize=8,stopbits=1,retries=3,handle_local_echo=False)

    ##\brief Connect to the server
    # \return True if succsessfully connected
    async def connect(self):
        if self.client:
            await client.connect()
            if not client.connected: client=None
        return (self.client!=None)

    ##\brief Read registers from the server
    # \param datablock Datablock to read from (di,co,hr or ir)
    # \param address Register address to read from
    # \return Decoded value, or None upon failure
    async def read(self,datablock,address):
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
        if datablock=='di' or datablock=='co': return response.bits[0]
        if datablock=='hr' or datablock=='ir': return Utils.decodeRegister(registerdata,response.registers)
        return None

    ##\brief Write registers to the server
    # \param datablock Datablock to write to (di,co,hr or ir)
    # \param address Register address to write to
    # \return True upon success
    async def write(self,datablock,address,value):
        response=None
        try:
            # Parse register information
            registerdata=self.profile['datablocks'][datablock][address]
            registeraddress=int(address)+self.offset
            values=Utils.encodeRegister(registerdata,value)

            # Execute request
            if datablock=='co': response = await self.client.write_coil(registeraddress,value,self.slaveid)
            if datablock=='hr': response = await self.client.write_registers(registeraddress,values,self.slaveid)
        except ModbusException as exc:
            logging.error('ModbusException: '+str(exc))
            return False
        if response==None:
            logging.warn('Can not write to input registers!')
            return False
        if response.isError() or isinstance(response, ExceptionResponse):
            logging.warning(str(response))
            return False
        return True

    ##\brief Read all registers from the server
    # \return dictionary of all read values
    async def download(self):
        output={}
        output['identity']=self.profile['identity']
        output['datablocks']={}
        for datablock in self.profile['datablocks']:
            for address in self.profile['datablocks'][datablock]:
                value=await self.read(datablock,address)
                if value:
                    if not datablock in output['datablocks']: output['datablocks'][datablock]={}
                    output['datablocks'][datablock][address]={}
                    output['datablocks'][datablock][address]['name']=self.profile['datablocks'][datablock][address]['dsc']
                    output['datablocks'][datablock][address]['value']=value
        return output

    ##\brief Close connection to server
    def close(self):
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
            self.client = ModbusClient.ModbusSerialClient(args.serial,framer=args.framer,baudrate=args.baudrate,parity=args.parity,timeout=args.timeout,strict=True,bytesize=8,stopbits=1,retries=3,handle_local_echo=False)

    ##\brief Connect to the server
    # \return True if succsessfully connected
    def connect(self):
        if self.client:
            self.client.connect()
            if not self.client.connected: self.client=None
        return (self.client!=None)

    ##\brief Read registers from the server
    # \param datablock Datablock to read from (di,co,hr or ir)
    # \param address Register address to read from
    # \return Decoded value, or None upon failure
    def read(self,datablock,address):
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
        if datablock=='di' or datablock=='co': return response.bits[0]
        if datablock=='hr' or datablock=='ir': return Utils.decodeRegister(registerdata,response.registers)
        return None

    ##\brief Write registers to the server
    # \param datablock Datablock to write to (di,co,hr or ir)
    # \param address Register address to write to
    # \return True upon success
    def write(self,datablock,address,value):
        response=None
        try:
            # Parse register information
            registerdata=self.profile['datablocks'][datablock][address]
            registeraddress=int(address)+self.offset
            values=Utils.encodeRegister(registerdata,value)

            # Execute request
            if datablock=='co': response = self.client.write_coil(registeraddress,value,self.slaveid)
            if datablock=='hr': response = self.client.write_registers(registeraddress,values,self.slaveid)
        except ModbusException as exc:
            logging.error('ModbusException: '+str(exc))
            return False
        if response==None:
            logging.warn('Can not write to input registers!')
            return False
        if response.isError() or isinstance(response, ExceptionResponse):
            logging.warning(str(response))
            return False
        return True

    ##\brief Read all registers from the server
    # \return dictionary of all read values
    def download(self):
        output={}
        output['identity']=self.profile['identity']
        output['datablocks']={}
        for datablock in self.profile['datablocks']:
            for address in self.profile['datablocks'][datablock]:
                value=self.read(datablock,address)
                if value:
                    if not datablock in output['datablocks']: output['datablocks'][datablock]={}
                    output['datablocks'][datablock][address]={}
                    output['datablocks'][datablock][address]['name']=self.profile['datablocks'][datablock][address]['dsc']
                    output['datablocks'][datablock][address]['value']=value
        return output

    ##\brief Close connection to server
    def close(self):
        if self.client: self.client.close()


##\class ClientWorker
# \brief Manages sending and receiving messages with the client object
class ClientWorker():
    ##\brief Initialize object
    # \param client Modbus client object to use (Fully connected)
    def __init__(self,client):
        # Parse registerlist
        self.client=client
        self.rcallbacks=[]
        self.wcallbacks=[]
        self.ccallbacks=[]
        self.reglist=[]
        self.backlog=[]
        self.started=None
        self.duration=0
        self.rcount=0
        self.wcount=0
        self.lock=threading.Lock()
        for datablock in self.client.profile['datablocks']:
            for address in self.client.profile['datablocks'][datablock]:
                self.reglist.append([datablock,address,None])

    ##\brief Add callback for register write
    # \param callback Callback function(datablock,register,value)
    def addWriteCallback(self,callback):
        self.wcallbacks.append(callback)

    ##\brief Add callback for register write
    # \param callback Callback function(datablock,register,value)
    def addReadCallback(self,callback):
        self.rcallbacks.append(callback)

    ##\brief Add callback for completed cycle
    # \param callback Callback function()
    def addCompletedCallback(self,callback):
        self.ccallbacks.append(callback)

    ##\brief Get status data
    # \return itemcount,readcount,writecount,duration,interval progress,read progress
    def getStatus(self):
        with self.lock:
            if self.next and self.interval:
                iprg=int((1-((self.next-time.time())/self.interval))*100)
            else:
                iprg=0
            if len(self.backlog):
                rprg=int((1-(len(self.backlog)/len(self.reglist)))*100)
            else:
                rprg=0
            return len(self.backlog),self.rcount,self.wcount,self.duration,iprg,rprg

    ##\brief Change polling interval
    # \param Interval Polling interval in seconds
    def setInterval(self,Interval):
        with self.lock:
            if self.interval!=Interval:
                self.interval=Interval
                if Interval:
                    logging.info('Changing polling interval to '+str(Interval)+'s')
                    self.next=time.time()
                else:
                    logging.info('Disabling polling interval')
                    self.next=None

    ##\brief Trigger an immidiate reading cycle
    def trigger(self):
        with self.lock:
            self.next=time.time()

    ##\brief Starts background thread
    def start(self):
        # Start poller thread
        self.running=True
        self.interval=60
        self.next=time.time()
        self.thread=threading.Thread(target=self.worker)
        self.thread.start()

    ##\brief Background thread to read/write values
    def worker(self):
        while self.running:
            with self.lock:
                # Get timestamp
                now=time.time()

                # Check for completed cycle
                if len(self.backlog)==0 and self.started:
                    duration=now-self.started
                    if self.duration==0: self.duration=duration
                    self.duration=(self.duration*3+(duration))/4.0
                    for callback in self.ccallbacks: callback()
                    logging.info('Cycle completed in %.3fms' % round(self.duration*1000,3))
                    self.started=None

                # Check for next cycle
                if self.next and now>=self.next and len(self.backlog)==0:
                    logging.info('Starting new read cycle')
                    self.backlog.extend(self.reglist)
                    self.started=now
                    if self.interval:
                        self.next=now+self.interval
                    else:
                        self.next=None

                # Iterate current cycle
                if len(self.backlog):
                    backlog=self.backlog[0]
                    self.backlog=self.backlog[1:]
                    if backlog[2]==None:
                        self.rcount+=1
                    else:
                        self.wcount+=1
                else:
                    backlog=None

            # Execute current cycle
            if backlog:
                if backlog[2]==None:
                    # Read register
                    value=self.client.read(backlog[0],backlog[1])
                    if value==None:
                        logging.warning('Failed to read register '+str(backlog[1]))
                    else:
                        self.client.profile['datablocks'][backlog[0]][str(backlog[1])]['value']=value
                        for callback in self.rcallbacks:
                            callback(backlog[0],backlog[1],value)
                else:
                    # Write register
                    if self.client.write(backlog[0],backlog[1],backlog[2]):
                        self.client.profile['datablocks'][backlog[0]][str(backlog[1])]['value']=backlog[2]
                        for callback in self.wcallbacks:
                            callback(backlog[0],backlog[1],backlog[2])
                    else:
                        logging.warning('Failed to write register '+str(backlog[1]))
            else:
                time.sleep(0.1)

    ##\brief Read a register value from server
    # \param datablock Name of datablock (di, co, hr or ir)
    # \param address Register address to read
    def read(self,datablock,address):
        with self.lock:
            logging.info('Reading register '+datablock+'['+str(address)+']')
            self.backlog.append([datablock,address,None])

    ##\brief Write a register value to server
    # \param datablock Name of datablock (di, co, hr or ir)
    # \param address Register address to write to
    # \param value Value to write
    def write(self,datablock,address,value):
        with self.lock:
            logging.info('Writing register '+datablock+'['+str(address)+']='+str(value))
            self.backlog.append([datablock,address,value])

    ##\brief Stop all running processes
    def close(self):
        self.running=False
        self.thread.join()

if __name__ == "__main__":
    # Parse command line options
    aboutstring=Utils.getAppName()+' Client '+Utils.getAppVersion()+'\n'
    aboutstring+='Client for MODBUS Testing\n'
    aboutstring+='Vegard Fiksdal(C)2024'
    args=Utils.parseArguments(aboutstring,-1)

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
    output=client.download()
    client.close()

    # Present options
    print(aboutstring+'\n')
    print(Utils.reportConfig(args))

    # Print result
    output=json.dumps(output,indent=4)
    print(str(output))

