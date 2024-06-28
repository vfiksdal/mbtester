
from qmbtserver import *
from mbtproxy import *

class ProxyUI(ServerUI):
    ##\brief Loads components and sets layout
    # \param args Parsed commandline arguments
    # \param parent Parent object
    def __init__(self,serverargs,clientargs,aboutstring,parent=None):
        super().__init__(serverargs,aboutstring,parent)
        self.setWindowTitle(App.getTitle('proxy'))
        self.hide()

        # Try to connect with dialog
        clientargs.profile=serverargs.profile
        self.aboutstring=aboutstring
        self.client=None
        while(True):
            if Connect(clientargs,'MODBUS Client Options',True).exec_()!=0:
                self.client=ClientObject(clientargs)
                if self.client.connect(): break
            else:
                logging.error('User aborted')
                sys.exit()
        for line in App.reportConfig(clientargs).split('\n'):
            self.conframe.addText(line)

        # Bind server and client
        self.proxy=ProxyObject(self.server,self.client)
        self.show()


if __name__ == "__main__":
    # Parse command line options
    aboutstring=App.getAbout('server','GUI proxy for MODBUS Testing')
    loader=Loader(gui=True)
    app=QApplication(sys.argv)
    window=ProxyUI(loader.serverargs,loader.clientargs,aboutstring)
    app.exec()
