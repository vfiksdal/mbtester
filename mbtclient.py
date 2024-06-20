##\package mbtclient
# \brief MBTester Client
#
# Vegard Fiksdal (C) 2024
#

# Import system modules
import logging.handlers
import sys,argparse,logging,threading,time

# Import QT modules
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar, QSplitter, QTreeView, QFrame, QStatusBar, QVBoxLayout, QScrollArea, QMenuBar, QMenu, QAction, QActionGroup, QTableWidget, QTableWidgetItem
from PyQt5.Qt import QStandardItemModel, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer

# Import local modules
from components import *
from mbclient import *

# Simple identification
appname='MBTester Client'
appversion='0.2.0'
application=appname+' '+appversion
aboutstring=application+'\n'
aboutstring+='GUI client for MODBUS Testing\n'
aboutstring+='Vegard Fiksdal(C)2024'

##\class ClientTableFrame
# \brief Table to hold and interact with a modbus register block
class ClientTableFrame(QFrame):
    ##\brief Constructor sets up frame layout
    # \param worker ClientWorker object to send/receive values
    # \param datablock Name of datablock (di, co, hr or ir)
    def __init__(self,worker,datablock):
        super().__init__()
        self.tablewidget=QTableWidget()
        self.tablewidget.verticalHeader().setVisible(False)
        self.tablewidget.horizontalHeader().setVisible(False)
        self.tablewidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablewidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablewidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablewidget.cellDoubleClicked.connect(self.DoubleClicked)
        layout=QVBoxLayout()
        layout.addWidget(self.tablewidget,1)
        self.setLayout(layout)
        Utils.setMargins(layout)
        self.lock=threading.Lock()
        self.datablock=datablock
        self.worker=worker
        self.updates=[]

        # Populate table
        registers=worker.client.profile['datablocks'][datablock]
        self.table=[['Description','Type','Access','Address','Value']]
        for register in registers:
            row=[]
            row.append(registers[register]['dsc'])
            row.append(registers[register]['dtype'])
            row.append(registers[register]['rtype'].upper())
            row.append(register)
            row.append('')
            self.table.append(row)
        self.tablewidget.setRowCount(len(self.table))
        self.tablewidget.setColumnCount(len(self.table[0]))
        for i in range(len(self.table)):
            for j in range(len(self.table[i])):
                self.tablewidget.setItem(i,j,QTableWidgetItem(str(self.table[i][j])))

    ##\brief Update read/write value
    # \param address Register address that has changed
    # \param value New register value
    #
    # This method only tags the changed value. The actual UI will be updated later on
    # the main UI thread -- See UpdateUI().
    def Update(self,address,value):
        with self.lock:
            self.updates.append([address,value])

    ##\brief Update UI controls
    #
    # This method updated the UI according to the register changes tracked by Update()
    def UpdateUI(self):
        with self.lock:
            updates=self.updates
            self.updates=[]
        for i in range(len(updates)):
            address=updates[i][0]
            value=updates[i][1]
            for j in range(len(self.table)):
                if self.table[j][3]==str(address):
                    self.tablewidget.setItem(j,4,QTableWidgetItem(str(value)))
                    self.worker.client.profile['datablocks'][self.datablock][str(address)]['value']=value
                    break

    ##\brief Event handler for double-clicks. Opens a dialog to write a register value
    # \param row The clicked row
    # \param column The clicked column (Not used)
    def DoubleClicked(self,row,column):
        address=self.table[row][3]
        register=self.worker.client.profile['datablocks'][self.datablock][address]
        if register['rtype'].upper()=='R':
            resp=QMessageBox.question(self,'Confirmation','This value is marked read-only.\n\nDo you want to try overwriting it anyway?')
            if resp==QMessageBox.StandardButton.No: return

        dialog=SetValue(register)
        if dialog.exec_()!=0:
            register['value']=dialog.value
            self.worker.Write(self.datablock,address,dialog.value)

##\class ClientWorker
# \brief Manages sending and receiving messages with the client object
class ClientWorker():
    ##\brief Initialize object
    # \param client Modbus client object to use (Fully connected)
    # \param callback Callback function to update register values
    def __init__(self,client,callback):
        # Parse registerlist
        self.client=client
        self.callback=callback
        self.reglist=[]
        self.backlog=[]
        self.start=None
        self.duration=0
        self.rcount=0
        self.wcount=0
        self.lock=threading.Lock()
        for datablock in self.client.profile['datablocks']:
            for address in self.client.profile['datablocks'][datablock]:
                self.reglist.append([datablock,address,None])

    ##\brief Get status data
    # \return itemcount,readcount,writecount,duration,interval progress,read progress
    def GetStatus(self):
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
    def SetInterval(self,Interval):
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
    def Trigger(self):
        with self.lock:
            self.next=time.time()

    ##\brief Starts background thread
    def Start(self):
        # Start poller thread
        self.running=True
        self.interval=60
        self.next=time.time()
        self.thread=threading.Thread(target=self.Worker)
        self.thread.start()

    ##\brief Background thread to read/write values
    def Worker(self):
        while self.running:
            with self.lock:
                now=time.time()
                if self.next and now>=self.next and len(self.backlog)==0:
                    logging.info('Starting new read cycle')
                    self.backlog.extend(self.reglist)
                    self.start=now
                    if self.interval:
                        self.next=now+self.interval
                    else:
                        self.next=None
                if len(self.backlog):
                    backlog=self.backlog[0]
                    self.backlog=self.backlog[1:]
                    if backlog[2]==None:
                        self.rcount+=1
                    else:
                        self.wcount+=1
                else:
                    if self.start:
                        duration=now-self.start
                        if self.duration==0: self.duration=duration
                        self.duration=(self.duration*3+(duration))/4.0
                        logging.info('Cycle completed in %.3fms' % round(self.duration*1000,3))
                        self.start=None
                    backlog=None

            if backlog:
                if backlog[2]==None:
                    value=self.client.Read(backlog[0],backlog[1])
                else:
                    value=None
                    if self.client.Write(backlog[0],backlog[1],backlog[2]): value=backlog[2]
                if value==None:
                    logging.warning('Failed to read/write register '+str(backlog[1]))
                elif self.callback:
                    self.callback(backlog[0],backlog[1],value)
            else:
                time.sleep(0.1)

    ##\brief Read a register value from server
    # \param datablock Name of datablock (di, co, hr or ir)
    # \param address Register address to read
    def Read(self,datablock,address):
        with self.lock:
            logging.info('Reading register '+datablock+'['+str(address)+']')
            self.backlog.append([datablock,address,None])

    ##\brief Write a register value to server
    # \param datablock Name of datablock (di, co, hr or ir)
    # \param address Register address to write to
    # \param value Value to write
    def Write(self,datablock,address,value):
        with self.lock:
            logging.info('Writing register '+datablock+'['+str(address)+']='+str(value))
            self.backlog.append([datablock,address,value])

    ##\brief Stop all running processes
    def Close(self):
        self.running=False
        self.thread.join()

##\class ClientUI
# \brief Main Application class
class ClientUI(QMainWindow):
    ##\brief Loads components and sets layout
    # \param args Parsed commandline arguments
    # \param parent Parent object
    def __init__(self,args,parent=None):
        super(ClientUI,self).__init__(parent)

        # Try to connect with dialog
        self.client=None
        self.conframe=ConFrame(args)
        while(True):
            if Connect(args,False).exec_()!=0:
                self.client=ClientObject(args)
                if self.client.Connect(): break
            else:
                logging.error('User aborted')
                sys.exit()
        self.worker=ClientWorker(self.client,self.Update)
        self.conframe.Clear()
        for line in aboutstring.split('\n'):
            self.conframe.AddText(line)
        self.conframe.AddText('')

        # Add statusbar
        self.statusbar=QStatusBar()
        self.status_int_progress=QProgressBar()
        self.status_read_progress=QProgressBar()
        self.status_rcount=QLineEdit()
        self.status_wcount=QLineEdit()
        self.status_queue=QLineEdit()
        self.status_duration=QLineEdit()
        self.status_int_progress.setEnabled(False)
        self.status_read_progress.setEnabled(False)
        self.status_rcount.setEnabled(False)
        self.status_wcount.setEnabled(False)
        self.status_queue.setEnabled(False)
        self.status_duration.setEnabled(False)
        self.statusbar.addWidget(self.status_rcount)
        self.statusbar.addWidget(self.status_wcount)
        self.statusbar.addWidget(self.status_queue)
        self.statusbar.addWidget(self.status_duration)
        self.statusbar.addWidget(self.status_int_progress,1)
        self.statusbar.addWidget(self.status_read_progress,1)
        self.setStatusBar(self.statusbar)
        self.status_int_progress.setAlignment(Qt.AlignCenter)
        self.status_int_progress.setTextVisible(True)
        self.status_read_progress.setAlignment(Qt.AlignCenter)
        self.status_read_progress.setTextVisible(True)
        self.statusbar.setVisible(True)
        
        # Build treeview
        self.treeview=QTreeView()
        self.treeview.setHeaderHidden(True)
        treemodel=QStandardItemModel()
        rootnode=treemodel.invisibleRootItem()
        logitem=StandardItem('Console')
        rootnode.appendRow(StandardItem('Discrete inputs'))
        rootnode.appendRow(StandardItem('Coils'))
        rootnode.appendRow(StandardItem('Holding registers'))
        rootnode.appendRow(StandardItem('Input registers'))
        rootnode.appendRow(logitem)

        # Wrap up treeview
        self.treeview.setModel(treemodel)
        self.treeview.expandAll()
        self.treeview.clicked.connect(self.TreeviewClick)
        index=treemodel.indexFromItem(logitem)
        self.treeview.setCurrentIndex(index)

        # Load frames for registers
        self.table_di=ClientTableFrame(self.worker,'di')
        self.table_co=ClientTableFrame(self.worker,'co')
        self.table_hr=ClientTableFrame(self.worker,'hr')
        self.table_ir=ClientTableFrame(self.worker,'ir')
        self.table_di.setVisible(False)
        self.table_co.setVisible(False)
        self.table_hr.setVisible(False)
        self.table_ir.setVisible(False)
        self.worker.Start()

        # Create menubar
        self.CreateMenubar()

        # Use a timer to process data from the queue
        self.timer=QTimer()
        self.timer.timeout.connect(self.Process)
        self.timer.start(250)

        # Show window
        layout=QVBoxLayout()
        widget=QFrame()
        scrollarea=QScrollArea()
        layout.addWidget(self.conframe)
        layout.addWidget(self.table_di)
        layout.addWidget(self.table_co)
        layout.addWidget(self.table_hr)
        layout.addWidget(self.table_ir)
        widget.setLayout(layout)
        scrollarea.setWidgetResizable(True)
        scrollarea.setWidget(widget)
        splitter=QSplitter(Qt.Horizontal)
        splitter.addWidget(self.treeview)
        splitter.addWidget(scrollarea)
        splitter.setSizes([200,500])
        self.setCentralWidget(splitter)
        self.setWindowTitle(application)
        self.resize(800,600)
        self.showMaximized()
        logging.debug('Loaded GUI components')

    ##\brief Stop background processes upon terminating the application
    # \param event Not used
    def closeEvent(self, event):
        self.timer.stop()
        logging.info('Shutting down connection')
        if self.worker: self.worker.Close()
        if self.client: self.client.Close()
        super().close()

    ##\brief Respond to user clicking on the treeview
    # \param Value The clicked item
    def TreeviewClick(self,Value):
        title=Value.data()
        self.table_di.setVisible(title=='Discrete inputs')
        self.table_co.setVisible(title=='Coils')
        self.table_hr.setVisible(title=='Holding registers')
        self.table_ir.setVisible(title=='Input registers')
        self.conframe.setVisible(title=='Console')

    ##\brief Callback to register updated values from client
    # \param datablock Type of data to update
    # \param address Regisster address
    # \param value New value
    def Update(self,datablock,address,value):
        if datablock=='di': self.table_di.Update(address,value)
        if datablock=='co': self.table_co.Update(address,value)
        if datablock=='hr': self.table_hr.Update(address,value)
        if datablock=='ir': self.table_ir.Update(address,value)

    ##\brief Timer event to update status and tranceivers in UI thread
    def Process(self):
        # Update registers
        self.table_di.UpdateUI()
        self.table_co.UpdateUI()
        self.table_hr.UpdateUI()
        self.table_ir.UpdateUI()

        # Update status bar
        icount,rcount,wcount,duration,iprg,rprg=self.worker.GetStatus()
        self.status_rcount.setText('Reads: %d' % rcount)
        self.status_wcount.setText('Writes: %d' % wcount)
        self.status_queue.setText('Queue: %d items' % icount)
        self.status_duration.setText('Tr: %.3fms' % round(duration*1000,3))
        if iprg:
            self.status_int_progress.setValue(iprg)
            self.status_int_progress.setFormat('Waiting for next read cycle '+str(iprg)+'%')
        else:
            self.status_int_progress.setValue(iprg)
            self.status_int_progress.setFormat('Automatic polling disabled')
        if rprg:
            self.status_read_progress.setValue(rprg)
            self.status_read_progress.setFormat('Executing read cycle '+str(rprg)+'%')
        else:
            self.status_read_progress.setValue(rprg)
            self.status_read_progress.setFormat('Read cycle completed')

    ##\brief Creates menu bar
    def CreateMenubar(self):
        # Create menu actions
        #saveprofile=lambda x: self.SaveTextToFile('Device Configuration','devcfg',x)
        action_saveprofile=QAction('Save profile',self)
        action_saveprofile.setStatusTip('Save current profile to file')
        action_saveprofile.triggered.connect(lambda: Utils.saveProfile(self.client.profile,self.GetFilename('Profile','json')))
        action_exit=QAction('Exit',self)
        action_exit.triggered.connect(lambda: self.close())
        action_setinterval_1s=QAction('1 second',self,checkable=True,checked=False)
        action_setinterval_1s.setStatusTip('Set polling interval to 1 second')
        action_setinterval_1s.triggered.connect(lambda: self.worker.SetInterval(1))
        action_setinterval_15s=QAction('15 seconds',self,checkable=True,checked=False)
        action_setinterval_15s.setStatusTip('Set polling interval to 15 seconds')
        action_setinterval_15s.triggered.connect(lambda: self.worker.SetInterval(15))
        action_setinterval_30s=QAction('30 seconds',self,checkable=True,checked=False)
        action_setinterval_30s.setStatusTip('Set polling interval to 30 seconds')
        action_setinterval_30s.triggered.connect(lambda: self.worker.SetInterval(30))
        action_setinterval_1m=QAction('1 minute',self,checkable=True,checked=True)
        action_setinterval_1m.setStatusTip('Set polling interval to 1 minute')
        action_setinterval_1m.triggered.connect(lambda: self.worker.SetInterval(60))
        action_setinterval_none=QAction('Disable',self,checkable=True,checked=False)
        action_setinterval_none.setStatusTip('Disable automatic polling')
        action_setinterval_none.triggered.connect(lambda: self.worker.SetInterval(None))
        action_setinterval_now=QAction('Read now',self)
        action_setinterval_now.setStatusTip('Trigger immidiate read-cycle')
        action_setinterval_now.triggered.connect(lambda: self.worker.Trigger())
        action_setinterval=QActionGroup(self)
        action_setinterval.addAction(action_setinterval_1s)
        action_setinterval.addAction(action_setinterval_15s)
        action_setinterval.addAction(action_setinterval_30s)
        action_setinterval.addAction(action_setinterval_1m)
        action_setinterval.addAction(action_setinterval_none)
        action_about=QAction('About '+application,self)
        action_about.triggered.connect(lambda: QMessageBox.about(self,'About','\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n'+aboutstring+'\n\n\n'))

        # Creating menus
        menubar = QMenuBar(self)
        filemenu = QMenu("&File", self)
        filemenu.addAction(action_saveprofile)
        filemenu.addSeparator()
        filemenu.addAction(action_exit)
        intmenu = QMenu("&Interval", self)
        intmenu.addAction(action_setinterval_1s)
        intmenu.addAction(action_setinterval_15s)
        intmenu.addAction(action_setinterval_30s)
        intmenu.addAction(action_setinterval_1m)
        intmenu.addAction(action_setinterval_none)
        intmenu.addSeparator()
        intmenu.addAction(action_setinterval_now)
        helpmenu = QMenu("&Help", self)
        helpmenu.addAction(action_about)
        menubar.addMenu(filemenu)
        menubar.addMenu(intmenu)
        menubar.addMenu(helpmenu)
        self.setMenuBar(menubar)

    ##\brief Saves text string to file
    # \param Desc Textual description of output file
    # \param Ext File extension to save as
    # \param Bin Text string to save
    # \param Returns filename
    def GetFilename(self,Desc,Ext):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        title='Save '+Desc
        default=Desc+'.'+Ext
        filter=Desc+'(*.'+Ext+');;All Files(*.*)'
        filename, _ = QFileDialog.getSaveFileName(self,title,default,filter,options=options)
        return filename


# Parse command line options
argformatter=lambda prog: argparse.RawTextHelpFormatter(prog,max_help_position=54)
parser=argparse.ArgumentParser(description=aboutstring,formatter_class=argformatter)
parser.add_argument('-c','--comm',choices=['tcp', 'udp', 'serial'],help='set communication, default is tcp',dest='comm',default='tcp',type=str)
parser.add_argument('-f','--framer',choices=['ascii', 'rtu', 'socket'],help='set framer, default depends on --comm',dest='framer',default='socket',type=str)
parser.add_argument('-s','--slaveid',help='set slave id',dest='slaveid',default=1,type=int)
parser.add_argument('-o','--offset',help='address offset',dest='offset',default=-1,type=int)
parser.add_argument('-H','--host',help='set host, default is 127.0.0.1',dest='host',default='127.0.0.1',type=str)
parser.add_argument('-P','--port',help='set tcp/udp/serial port',dest='port',default='502',type=str)
parser.add_argument('-b','--baudrate',help='set serial device baud rate',dest='baudrate',default=9600,type=int)
parser.add_argument('-x','--parity',choices=['O', 'E', 'N'],help='set serial device parity',dest='parity',default='N',type=str)
parser.add_argument('-i','--interval',help='set read interval in seconds',dest='interval',default=10,type=float)
parser.add_argument('-t','--timeout',help='set request timeout',dest='timeout',default=1,type=int)
parser.add_argument('-l','--log',choices=['critical', 'error', 'warning', 'info', 'debug'],help='set log level, default is info',dest='log',default='info',type=str)
parser.add_argument('-p','--profile',help='modbus register profile to serve',dest='profile',default='',type=str)
args = parser.parse_args()

# Load application window and start application
app=QApplication(sys.argv)
window=ClientUI(args)
app.exec()
