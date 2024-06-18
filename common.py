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
        if os.path.isfile(filename):
            fd=open(filename,'r')
            profile=json.loads(fd.read())
            fd.close()
        else:
            raise Exception('Unknown profile: '+filename)

        # Assert register descriptions
        for datablock in profile['datablocks']:
            for register in profile['datablocks'][datablock]:
                if not 'bo' in profile['datablocks'][datablock][register]: profile['datablocks'][datablock][register]['bo']='<'
                if not 'wo' in profile['datablocks'][datablock][register]: profile['datablocks'][datablock][register]['wo']='<'
                if not 'rtype' in profile['datablocks'][datablock][register]: profile['datablocks'][datablock][register]['rtype']='rw'
                if not 'dtype' in profile['datablocks'][datablock][register]: profile['datablocks'][datablock][register]['dtype']='uint16'
                if not 'dsc' in profile['datablocks'][datablock][register]: profile['datablocks'][datablock][register]['dsc']='Unknown'
                if not 'value' in profile['datablocks'][datablock][register]: profile['datablocks'][datablock][register]['value']=0
        return profile

    ##\brief Counts number of 16-bit registers for datatype
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
        if profile['dtype']=='string':
            l=len(profile['value'])
            if l%2==0: return int(l/2)
            else: return int(l/2+1)
        print('Sizing unknown datatype: '+str(profile['dtype']))

    ##\brief Saves current profile to disk (With current values)
    # \param profile Profile dictionary
    # \param filename Filename to save as
    def saveProfile(profile,filename):
        if len(filename):
            fd=open(filename,'w')
            fd.write(json.dumps(profile,indent=4))
            fd.close()

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
        elif profile['dtype']=='string':    builder.add_string(value)
        else: print('Encoding unknown datatype: '+str(profile['dtype']))
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
        elif profile['dtype']=='string':    value = decoder.decode_string(len(profile['value'])).decode('utf-8')
        else: print('Decoding unknown datatype: '+str(profile['dtype']))
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
