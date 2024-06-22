##\package common
# \brief MBTester utilities
#
# Vegard Fiksdal (C) 2024
#
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.datastore import ModbusSparseDataBlock
import json,logging,sys,os,argparse,struct

##\class Utils
# \brief Utilities for loading profiles, handling register values etc
class Utils():
    ##\brief Get application name
    # \return MBTester
    def getAppName():
        return 'MBTester'

    ##\brief Get application version
    # \return Current version as a string
    def getAppVersion():
        return '0.3.0'

    ##\brief Parse commandline arguments
    # \param about String to describe program
    # \param offset Default register address offset
    # \return Parsed arguments as an object
    #
    # The offset will typically be 0 for a server, and -1 for a client due to modbus oddness.
    def parseArguments(about,offset=0):
        argformatter=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=54)
        parser=argparse.ArgumentParser(description=about,formatter_class=argformatter)
        parser.add_argument('-c','--comm',choices=['tcp', 'udp', 'serial'],help='Communication interface, default is tcp',dest='comm',default='tcp',type=str)
        parser.add_argument('-f','--framer',choices=['ascii', 'rtu', 'socket'],help='MODBUS framer, default is rtu',dest='framer',default='rtu',type=str)
        parser.add_argument('-s','--slaveid',help='Slave id',dest='slaveid',default=1,type=int)
        parser.add_argument('-o','--offset',help='Register address offset (client only)',dest='offset',default=offset,type=int)
        parser.add_argument('-H','--host',help='Network host, default is 127.0.0.1',dest='host',default='127.0.0.1',type=str)
        parser.add_argument('-P','--port',help='TCP/UDP network port',dest='port',default='502',type=str)
        parser.add_argument('-S','--serial',help='Serial device port name',dest='serial',default='COM1',type=str)
        parser.add_argument('-b','--baudrate',help='Serial device baud rate',dest='baudrate',default=9600,type=int)
        parser.add_argument('-x','--parity',choices=['O', 'E', 'N'],help='Serial device parity',dest='parity',default='N',type=str)
        parser.add_argument('-t','--timeout',help='Request timeout',dest='timeout',default=1,type=int)
        parser.add_argument('-p','--profile',help='MODBUS register profile to serve',dest='profile',default='',type=str)
        parser.add_argument('-l','--log',choices=['critical', 'error', 'warning', 'info', 'debug'],help='Log level, default is info',dest='log',default='info',type=str)
        return parser.parse_args()

    ##\brief Get path of application
    # \return Application path as a string
    def getPath():
        return str(os.path.dirname(os.path.abspath(sys.argv[0]))+os.path.sep)

    ##\brief List profiles in application path
    # \return List .json files in the application path
    def listProfiles():
        files=[]
        path=Utils.getPath()
        allfiles=os.listdir(path)
        for file in allfiles:
            if file.upper().endswith('.JSON'):
                files.append(path+file)
        return files

    ##\brief Load profile from file or memory
    # \param filename Filename or name of predefined profile
    # \return Loaded profile
    def loadProfile(filename):
        # Read and parse json input
        if os.path.isfile(filename):
            fd=open(filename,'r')
            profile=json.loads(fd.read())
            fd.close()
        else:
            raise Exception('Unknown profile: '+filename)

        # Sanitize register metadata
        if not 'datablocks' in profile: profile['datablocks']={}
        if not 'di' in profile['datablocks']: profile['datablocks']['di']={}
        if not 'co' in profile['datablocks']: profile['datablocks']['co']={}
        if not 'hr' in profile['datablocks']: profile['datablocks']['hr']={}
        if not 'ir' in profile['datablocks']: profile['datablocks']['ir']={}
        for datablock in profile['datablocks']:
            for register in profile['datablocks'][datablock]:
                # Set defaults according to type
                register=profile['datablocks'][datablock][register]
                if datablock=='di' or datablock=='co':
                    register['dtype']='bit'
                if datablock=='di' or datablock=='ir':
                    register['rtype']='r'
                if datablock=='co' or datablock=='hr':
                    if not 'rtype' in register: register['rtype']='rw'
                if datablock=='hr' or datablock=='ir':
                    if not 'rtype' in register: register['dtype']='int16'

                # Set generic defaults
                if not 'dsc' in register: register['dsc']='Unknown'
                if not 'value' in register: register['value']=0
                if not 'bo' in register: register['bo']='<'
                if not 'wo' in register: register['wo']='<'

                # Assert value formatting
                register['value']=Utils.castRegister(register,register['value'])

        return profile

    ##\brief Saves current profile to disk (With current values)
    # \param profile Profile dictionary
    # \param filename Filename to save as
    def saveProfile(profile,filename):
        if len(filename):
            fd=open(filename,'w')
            fd.write(json.dumps(profile,indent=4))
            fd.close()

    ##\brief Reports configuration
    # \param args Commandline arguments to report
    # \return Configuration report as a string
    def reportConfig(args):
        s=''
        s+='%-*s: %s\n' % (30,'Communication interface',args.comm.upper())
        s+='%-*s: %s\n' % (30,'MODBUS framer',args.framer.upper())
        s+='%-*s: %s\n' % (30,'MODBUS profile',os.path.basename(args.profile))
        s+='%-*s: %s\n' % (30,'MODBUS slave ID',str(args.slaveid))
        #s+='%-*s: %s\n' % (30,'MODBUS offset',str(args.offset))
        if args.comm=='serial':
            s+='%-*s: %s\n' % (30,'Serial port',args.serial)
            s+='%-*s: %s\n' % (30,'Baudrate',args.baudrate)
            s+='%-*s: %s\n' % (30,'Parity',Utils.getParityName(args.parity))
        else:
            s+='%-*s: %s\n' % (30,'Network host',args.host)
            s+='%-*s: %s\n' % (30,'Network port',args.port)
        return s

    ##\brief Get name of parity setting (Eg. E=Even)
    # \param argument Parity commandline argument
    # \return Name of parity setting
    def getParityName(argument):
        if argument=='N': return 'None'
        if argument=='E': return 'Even'
        if argument=='O': return 'Odd'
        return 'Error'
    
    ##\brief Get name of data blocks
    # \param argument Block abbrevation (di,co,hr,ir)
    # \return Name of data block
    def getDatablockName(argument):
        if argument=='di': return 'Discrete input'
        if argument=='co': return 'Coil'
        if argument=='hr': return 'Holding register'
        if argument=='ir': return 'Input register'

    ##\brief Minimizes margins of a QT layout
    # \param layout Layout to minimize
    def setMargins(layout):
        layout.setContentsMargins(0,0,0,0)

    ##\brief Counts number of registers for datatype
    # \param register The register block to evaluate
    # \return Number of registers for value
    def registersPerValue(register):
        if register['dtype']=='float16': return 1
        if register['dtype']=='float32': return 2
        if register['dtype']=='float64': return 4
        if register['dtype']=='uint32':  return 2
        if register['dtype']=='uint16':  return 1
        if register['dtype']=='uint8':   return 1
        if register['dtype']=='int32':   return 2
        if register['dtype']=='int16':   return 1
        if register['dtype']=='int8':    return 1
        if register['dtype']=='float':   return 2
        if register['dtype']=='double':  return 4
        if register['dtype']=='word':    return 1
        if register['dtype']=='int':     return 2
        if register['dtype']=='bit':     return 1
        if register['dtype']=='string':
            l=len(register['value'])
            if l%2==0: return int(l/2)
            else: return int(l/2+1)
        logging.error('Sizing unknown datatype: '+str(register['dtype']))

    ##\brief Encode scalar value to register values
    # \param register Register profile
    # \param value Decoded value
    # \return List of register values
    def encodeRegister(register,value):
        builder = BinaryPayloadBuilder(byteorder=register['bo'], wordorder=register['wo'])
        if register['dtype']=='float16':     builder.add_16bit_float(value)
        elif register['dtype']=='float32':   builder.add_32bit_float(value)
        elif register['dtype']=='float64':   builder.add_64bit_float(value)
        elif register['dtype']=='uint32':    builder.add_32bit_uint(value)
        elif register['dtype']=='uint16':    builder.add_16bit_uint(value)
        elif register['dtype']=='uint8':     builder.add_8bit_uint(value)
        elif register['dtype']=='int32':     builder.add_32bit_int(value)
        elif register['dtype']=='int16':     builder.add_16bit_int(value)
        elif register['dtype']=='int8':      builder.add_8bit_int(value)
        elif register['dtype']=='float':     builder.add_32bit_float(value)
        elif register['dtype']=='double':    builder.add_64bit_float(value)
        elif register['dtype']=='word':      builder.add_16bit_int(value)
        elif register['dtype']=='int':       builder.add_32bit_int(value)
        elif register['dtype']=='bit':       builder.add_bits([value])
        elif register['dtype']=='string':    builder.add_string(value)
        else: logging.error('Encoding unknown datatype: '+str(register['dtype']))
        return builder.to_registers()

    ##\brief Decode register values to a scalar value
    # \param register Register profile
    # \param values List of register values
    # \return Decoded value
    def decodeRegister(register,values):
        decoder = BinaryPayloadDecoder.fromRegisters(values, byteorder=register['bo'], wordorder=register['wo'])
        value = None
        if register['dtype']=='float16':     value = decoder.decode_16bit_float()
        elif register['dtype']=='float32':   value = decoder.decode_32bit_float()
        elif register['dtype']=='float64':   value = decoder.decode_64bit_float()
        elif register['dtype']=='uint32':    value = decoder.decode_32bit_uint()
        elif register['dtype']=='uint16':    value = decoder.decode_16bit_uint()
        elif register['dtype']=='uint8':     value = decoder.decode_8bit_uint()
        elif register['dtype']=='int32':     value = decoder.decode_32bit_int()
        elif register['dtype']=='int16':     value = decoder.decode_16bit_int()
        elif register['dtype']=='int8':      value = decoder.decode_8bit_int()
        elif register['dtype']=='float':     value = decoder.decode_32bit_float()
        elif register['dtype']=='double':    value = decoder.decode_64bit_float()
        elif register['dtype']=='word':      value = decoder.decode_16bit_int()
        elif register['dtype']=='int':       value = decoder.decode_32bit_int()
        elif register['dtype']=='bit':
            value = decoder.decode_bits()
            if len(value)>1: value=value[0]
        elif register['dtype']=='string':
            value = decoder.decode_string(len(register['value'])).decode('utf-8')
        else: logging.error('Decoding unknown datatype: '+str(register['dtype']))
        return value


    ##\brief Cast value to instric register type
    # \param register Register profile
    # \param value Potentially erroniously typed value, typically a string representation
    # \return Decoded value
    #
    # This is likely to raise an exception. Always try-catch this one properly
    def castRegister(register,value):
        if register['dtype']=='float16':     value=struct.unpack('e',struct.pack('e',float(value)))[0]
        elif register['dtype']=='float32':   value=struct.unpack('f',struct.pack('f',float(value)))[0]
        elif register['dtype']=='float64':   value=struct.unpack('d',struct.pack('d',float(value)))[0]
        elif register['dtype']=='uint32':    value=struct.unpack('I',struct.pack('I',int(value)))[0]
        elif register['dtype']=='uint16':    value=struct.unpack('H',struct.pack('H',int(value)))[0]
        elif register['dtype']=='uint8':     value=struct.unpack('B',struct.pack('B',int(value)))[0]
        elif register['dtype']=='int32':     value=struct.unpack('i',struct.pack('i',int(value)))[0]
        elif register['dtype']=='int16':     value=struct.unpack('h',struct.pack('h',int(value)))[0]
        elif register['dtype']=='int8':      value=struct.unpack('b',struct.pack('b',int(value)))[0]
        elif register['dtype']=='float':     value=struct.unpack('f',struct.pack('f',float(value)))[0]
        elif register['dtype']=='double':    value=struct.unpack('d',struct.pack('d',float(value)))[0]
        elif register['dtype']=='word':      value=struct.unpack('h',struct.pack('h',int(value)))[0]
        elif register['dtype']=='int':       value=struct.unpack('i',struct.pack('i',int(value)))[0]
        elif register['dtype']=='bit':
            if isinstance(value,str) and (value.upper()=='FALSE' or value=='0'):
                value=False
            else:
                value=bool(value)
        elif register['dtype']=='string':
            length=len(register['value'])
            value=value[:length]
            while len(value)<length: value+=' '
        return value

##\class DataBlock
# \brief Retains modbus registers in memory
class DataBlock(ModbusSparseDataBlock):
    ##\brief Initiates data storage and loads profile
    # \param profile Modbus registers to load
    def __init__(self, profile, datablock):
        self.rcallbacks=[]
        self.wcallbacks=[]
        self.profile=profile
        self.datablock=datablock
        registers={}
        for key in profile['datablocks'][datablock]:
            register=profile['datablocks'][datablock][key]
            logging.debug('Setting register['+key+']='+str(register['value']))
            registers[int(key)]=Utils.encodeRegister(register,register['value'])
        super().__init__(registers)

    ##\brief Add callback for register write
    # \param callback Callback function(datablock,register,value)
    def AddWriteCallback(self,callback):
        self.wcallbacks.append(callback)

    ##\brief Add callback for register write
    # \param callback Callback function(datablock,register,value)
    def AddReadCallback(self,callback):
        self.rcallbacks.append(callback)

    ##\brief Overwrites modbus registers and calls optional callback
    # \param address Register address to write to
    # \param value Values to write
    def setValues(self, address, value):
        super().setValues(address,value)
        self.profile['datablocks'][self.datablock][str(address)]['value']=value
        for callback in self.wcallbacks:
            callback(self.datablock,address,value)

    ##\brief Get modbus register contents
    # \param address Register address to read from
    # \param count Number of 16-bit registers to read
    def getValues(self, address, count=1):
        values = super().getValues(address,count)
        for callback in self.rcallbacks:
            callback(self.datablock,address,values)
        return values

    ##\brief Validate modbus register contents
    # \param address Register address to validate
    # \param count Number of 16-bit registers to validate
    def validate(self, address, count=1):
        return super().validate(address,count)
