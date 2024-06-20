##\package common
# \brief MBTester utilities
#
# Vegard Fiksdal (C) 2024
#
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.datastore import ModbusSparseDataBlock
import json,logging,sys,os

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
        return '0.2.0'

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

    ##\brief Minimizes margins of a QT layout
    # \param layout Layout to minimize
    def setMargins(layout):
        layout.setContentsMargins(0,0,0,0)

    ##\brief Counts number of registers for datatype
    # \param profile The register block to evaluate
    # \return Number of registers for value
    def registersPerValue(profile):
        if profile['dtype']=='float16': return 1
        if profile['dtype']=='float32': return 2
        if profile['dtype']=='float64': return 4
        if profile['dtype']=='uint32':  return 2
        if profile['dtype']=='uint16':  return 1
        if profile['dtype']=='uint8':   return 1
        if profile['dtype']=='int32':   return 2
        if profile['dtype']=='int16':   return 1
        if profile['dtype']=='int8':    return 1
        if profile['dtype']=='float':   return 2
        if profile['dtype']=='double':  return 4
        if profile['dtype']=='word':    return 1
        if profile['dtype']=='int':     return 2
        if profile['dtype']=='bit':     return 1
        if profile['dtype']=='string':
            l=len(profile['value'])
            if l%2==0: return int(l/2)
            else: return int(l/2+1)
        logging.error('Sizing unknown datatype: '+str(profile['dtype']))

    ##\brief Encode scalar value to register values
    # \param profile Register profile
    # \param value Decoded value
    # \return List of register values
    def encodeRegister(profile,value):
        builder = BinaryPayloadBuilder(byteorder=profile['bo'], wordorder=profile['wo'])
        if profile['dtype']=='float16':     builder.add_16bit_float(value)
        elif profile['dtype']=='float32':   builder.add_32bit_float(value)
        elif profile['dtype']=='float64':   builder.add_64bit_float(value)
        elif profile['dtype']=='uint32':    builder.add_32bit_uint(value)
        elif profile['dtype']=='uint16':    builder.add_16bit_uint(value)
        elif profile['dtype']=='uint8':     builder.add_8bit_uint(value)
        elif profile['dtype']=='int32':     builder.add_32bit_int(value)
        elif profile['dtype']=='int16':     builder.add_16bit_int(value)
        elif profile['dtype']=='int8':      builder.add_8bit_int(value)
        elif profile['dtype']=='float':     builder.add_32bit_float(value)
        elif profile['dtype']=='double':    builder.add_64bit_float(value)
        elif profile['dtype']=='word':      builder.add_16bit_int(value)
        elif profile['dtype']=='int':       builder.add_32bit_int(value)
        elif profile['dtype']=='bit':       builder.add_bits([value])
        elif profile['dtype']=='string':    builder.add_string(value)
        else: logging.error('Encoding unknown datatype: '+str(profile['dtype']))
        return builder.to_registers()

    ##\brief Decode register values to a scalar value
    # \param profile Register profile
    # \param register List of register values
    # \return Decoded value
    def decodeRegister(profile,register):
        decoder = BinaryPayloadDecoder.fromRegisters(register, byteorder=profile['bo'], wordorder=profile['wo'])
        value = None
        if profile['dtype']=='float16':     value = decoder.decode_16bit_float()
        elif profile['dtype']=='float32':   value = decoder.decode_32bit_float()
        elif profile['dtype']=='float64':   value = decoder.decode_64bit_float()
        elif profile['dtype']=='uint32':    value = decoder.decode_32bit_uint()
        elif profile['dtype']=='uint16':    value = decoder.decode_16bit_uint()
        elif profile['dtype']=='uint8':     value = decoder.decode_8bit_uint()
        elif profile['dtype']=='int32':     value = decoder.decode_32bit_int()
        elif profile['dtype']=='int16':     value = decoder.decode_16bit_int()
        elif profile['dtype']=='int8':      value = decoder.decode_8bit_int()
        elif profile['dtype']=='float':     value = decoder.decode_32bit_float()
        elif profile['dtype']=='double':    value = decoder.decode_64bit_float()
        elif profile['dtype']=='word':      value = decoder.decode_16bit_int()
        elif profile['dtype']=='int':       value = decoder.decode_32bit_int()
        elif profile['dtype']=='bit':
            value = decoder.decode_bits()
            if len(value)>1: value=value[0]
        elif profile['dtype']=='string':
            value = decoder.decode_string(len(profile['value'])).decode('utf-8')
        else: logging.error('Decoding unknown datatype: '+str(profile['dtype']))
        return value


    ##\brief Cast value to instric register type
    # \param profile Register profile
    # \param value Potentially erroniously typed value, typically a string representation
    # \return Decoded value
    #
    # This is very likely to raise an exception. Always try-catch this one properly
    def castRegister(profile,value):
        if profile['dtype']=='float16':     value=float(value)
        elif profile['dtype']=='float32':   value=float(value)
        elif profile['dtype']=='float64':   value=float(value)
        elif profile['dtype']=='uint32':    value=int(value)
        elif profile['dtype']=='uint16':    value=int(value)
        elif profile['dtype']=='uint8':     value=int(value)
        elif profile['dtype']=='int32':     value=int(value)
        elif profile['dtype']=='int16':     value=int(value)
        elif profile['dtype']=='int8':      value=int(value)
        elif profile['dtype']=='float':     value=float(value)
        elif profile['dtype']=='double':    value=float(value)
        elif profile['dtype']=='word':      value=int(value)
        elif profile['dtype']=='int':       value=int(value)
        elif profile['dtype']=='bit':
            if isinstance(value,str) and (value.upper()=='FALSE' or value=='0'):
                value=False
            else:
                value=bool(value)
        elif profile['dtype']=='string':
            length=len(profile['value'])
            value=value[:length]
            while len(value)<length: value+=' '
        return value

##\class DataBlock
# \brief Retains modbus registers in memory
class DataBlock(ModbusSparseDataBlock):
    ##\brief Initiates data storage and loads profile
    # \param profile Modbus registers to load
    def __init__(self, profile):
        self.cb_read=None
        self.cb_write=None
        registers={}
        for key in profile:
            logging.debug('Setting register['+key+']='+str(profile[key]['value']))
            registers[int(key)]=Utils.encodeRegister(profile[key],profile[key]['value'])
        super().__init__(registers)

    ##\brief Overwrites modbus registers and calls optional callback
    # \param address Register address to write to
    # \param value Values to write
    def setValues(self, address, value):
        super().setValues(address, value)
        if self.cb_write: self.cb_write(address,value)

    ##\brief Get modbus register contents
    # \param address Register address to read from
    # \param count Number of 16-bit registers to read
    def getValues(self, address, count=1):
        values = super().getValues(address, count=count)
        if self.cb_read: self.cb_read(address,values)
        return values

    ##\brief Validate modbus register contents
    # \param address Register address to validate
    # \param count Number of 16-bit registers to validate
    def validate(self, address, count=1):
        return super().validate(address, count=count)
