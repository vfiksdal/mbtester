
from qmbtserver import *
from mbtproxy import *

class ProxyUI(ServerUI):
    ##\brief Loads components and sets layout
    # \param args Parsed commandline arguments
    # \param parent Parent object
    def __init__(self,serverargs,clientargs,aboutstring):
        super().__init__(serverargs,aboutstring,False)
        self.setWindowTitle(App.getTitle('proxy'))
        self.hide()

        # Try to connect with dialog
        self.worker=None
        self.conframe.showMessagebox(True)
        clientargs.profile=serverargs.profile
        self.aboutstring=aboutstring
        self.client=None
        while(True):
            if Connect(clientargs,'MODBUS Client Options',True).exec_()!=0:
                mtcp=(clientargs.comm=='tcp' and serverargs.comm=='tcp')
                mudp=(clientargs.comm=='udp' and serverargs.comm=='udp')
                mhost=(clientargs.host==serverargs.host)
                mport=(clientargs.port==serverargs.port)
                if (mtcp or mudp) and mhost and mport:
                    logging.error('Server and client is the same!')
                    continue
                self.client=ClientObject(clientargs)
                if self.client.connect(): break
            else:
                logging.error('User aborted')
                self.close()
                sys.exit()
        self.conframe.showMessagebox(False)
        for line in App.reportConfig(clientargs).split('\n'):
            self.conframe.addText(line)

        # Temporarily load worker to read current values
        self.worker=ClientWorker(self.client)
        self.worker.addReadCallback(self.updateWrite)
        self.worker.addCompletedCallback(self.updateComplete)
        self.worker.start()

        # Bind server and client
        self.proxy=ProxyObject(self.server,self.client)
        self.showMaximized()

    ##\brief Update read/write value
    # \param datablock Datablock containing register
    # \param address Register address that has changed
    # \param value New register value
    # \return Original value
    def updateWrite(self,datablock,address,value):
        value=Registers.encodeRegister(self.client.profile['datablocks'][datablock][str(address)],value)
        if datablock=='di': self.table_di.updateWrite(datablock,address,value)
        if datablock=='co': self.table_co.updateWrite(datablock,address,value)
        if datablock=='hr': self.table_hr.updateWrite(datablock,address,value)
        if datablock=='ir': self.table_ir.updateWrite(datablock,address,value)

    ##\brief Close worker after initial read
    def updateComplete(self):
        logging.info('Read initial server values')
        self.worker.running=False

    ##\brief Stop background processes upon terminating the application
    # \param event Not used
    def closeEvent(self, event):
        if self.worker: self.worker.close()
        if self.client: self.client.close()
        super().closeEvent(event)

if __name__ == "__main__":
    # Parse command line options
    aboutstring=App.getAbout('server','GUI proxy for MODBUS Testing')
    loader=Loader(gui=True)
    app=QApplication(sys.argv)
    window=ProxyUI(loader.serverargs,loader.clientargs,aboutstring)
    app.exec()
