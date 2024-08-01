##\package jsonformatter
# \brief Simple script to standardize formatting of profile files
#
# Vegard Fiksdal (C) 2024
#
import json,sys

##\class JSONFormatter
# \brief Class to prettyprint json data
class JSONFormatter():
    ##\brief Initialize formatter
    # \param indent Number of whitespaces for each indentation
    # \param depth Max number of indentations
    # \param quote Quotation marks in output
    def __init__(self,indent=4,depth=3,quote='"'):
        self.indent=indent
        self.depth=depth
        self.quote=quote

    ##\brief Read and parse contents of a file
    # \param filename Path to input file
    # \return JSON string
    def parseFile(self,filename):
        data='{}'
        with open(filename,'r') as fd:
            data=fd.read()
        return self.parseString(data)

    ##\brief Parse json formatted string
    # \param string json string to format
    # \return JSON string
    def parseString(self,string):
        data=json.loads(string)
        return self.parseDict(data)

    ##\brief Recursively format a dictionary object
    # \param object Python dictionary object to parse
    # \param depth Current number of indentations to apply
    # \return JSON string representing the _data object
    def parseDict(self,object,depth=0):
        s=''
        if type(object)==dict:
            s+='{'
            depth+=1
            for key in object.keys():
                if depth<=self.depth:
                    s+='\n'+' '*self.indent*depth
                else:
                    s+=' '
                s+=self.quote+key+self.quote+':'
                s+=self.parseDict(object[key],depth)+','
            if len(object.keys()): s=s[:-1]
            depth-=1
            if depth<self.depth: s+='\n'+' '*self.indent*depth
            s+='}'
        else:
            s+=self.quote+str(object)+self.quote
        return s

if __name__ == "__main__":
    if len(sys.argv)<2 or len(sys.argv)>3:
        print('Usage: '+sys.argv[0]+' INPUTFILE [OUTPUTFILE]')
        sys.exit()
    object=JSONFormatter(4,3,'"')
    string=object.parseFile(sys.argv[1])
    if len(sys.argv)==3:
        with open(sys.argv[2],'w') as fd:
            fd.write(string)
        print(str(len(string))+' bytes written to '+sys.argv[2])
    else:
        print(string)

