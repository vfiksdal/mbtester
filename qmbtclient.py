##\package mbtclient
# \brief MBTester Client using Qt
#
# Vegard Fiksdal (C) 2024
#

# Import system modules
import logging.handlers
import sys,logging

# Import QT modules
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar, QSplitter, QTreeView, QStatusBar, QScrollArea, QMenuBar, QMenu, QAction, QActionGroup, QSpinBox
from PyQt5.Qt import QStandardItemModel
from PyQt5.QtCore import Qt, QTimer

# Import local modules
from components import *
from mbtclient import *

class LabeledControl(QFrame):
    def __init__(self,label,control):
        super().__init__()
        hlayout=QHBoxLayout()
        hlayout.addWidget(QLabel(label),1)
        hlayout.addWidget(control,1)
        self.setLayout(hlayout)

##\class DeviceIdFrame
# \brief Frame to send and receive identification MODBUS requests to device
class DeviceIdFrame(QFrame):
    def __init__(self,worker):
        super().__init__()
        self.worker=worker
        self.client=worker.client.client
        self.args=worker.client.args
        self.deviceid=QSpinBox()
        self.function=QComboBox()
        self.log=QListWidget()
        button=QPushButton('Execute')
        layout=QVBoxLayout()
        layout.addWidget(LabeledControl('Device ID',self.deviceid))
        layout.addWidget(LabeledControl('Function',self.function))
        layout.addWidget(LabeledControl('',button))
        layout.addWidget(self.log,1)
        self.deviceid.setRange(0,248)
        self.deviceid.setValue(self.args.deviceid)
        self.function.addItem('01 - Basic Device Identification')
        self.function.addItem('02 - Regular Device Identification')
        self.function.addItem('03 - Extended Device Identification')
        self.function.setCurrentIndex(0)
        self.log.setFont(QFont('cascadia mono'))
        button.clicked.connect(self.Execute)
        self.setLayout(layout)

    def Execute(self):
        self.worker.setPaused(True)
        self.log.clear()
        deviceid=self.deviceid.value()
        devicefnc=self.function.currentIndex()+1
        try:
            response=self.client.read_device_information(devicefnc,slave=deviceid)
        except ModbusException as exc:
            self.log.addItem('Exception: '+str(exc))
            response=None
        if response!=None and (response.isError() or isinstance(response, ExceptionResponse)):
            self.log.addItem('Error: '+str(response))
            response=None
        if response!=None:
            for key in response.information.keys():
                self.log.addItem(response.information[key].decode('utf-8'))
        self.worker.setPaused(False)



##\class CustomClientFrame
# \brief Frame to send and receive custom MODBUS requests to device
class CustomClientFrame(QFrame):
    def __init__(self,worker):
        super().__init__()
        self.worker=worker
        self.client=worker.client.client
        self.args=worker.client.args
        self.deviceid=QSpinBox()
        self.function=QComboBox()
        self.address=QSpinBox()
        self.count=QSpinBox()
        self.border=QComboBox()
        self.worder=QComboBox()
        self.log=QListWidget()
        button=QPushButton('Execute')
        layout=QVBoxLayout()
        layout.addWidget(LabeledControl('Device ID',self.deviceid))
        layout.addWidget(LabeledControl('Function',self.function))
        layout.addWidget(LabeledControl('Address',self.address))
        layout.addWidget(LabeledControl('Count',self.count))
        layout.addWidget(LabeledControl('Word order',self.worder))
        layout.addWidget(LabeledControl('Byte order',self.border))
        layout.addWidget(LabeledControl('',button))
        layout.addWidget(self.log,1)
        self.deviceid.setRange(0,248)
        self.deviceid.setValue(self.args.deviceid)
        self.address.setRange(0,65536)
        self.address.setValue(1)
        self.count.setRange(1,16)
        self.count.setValue(1)
        self.function.addItem('01 - Read Coils')
        self.function.addItem('02 - Read Discrete Inputs')
        self.function.addItem('03 - Read Holding Registers')
        self.function.addItem('04 - Read Input Registers')
        self.function.addItem('05 - Write single Coil')
        self.function.addItem('06 - Write single Register')
        self.function.addItem('15 - Write multiple Coils')
        self.function.addItem('16 - Write multiple Registers')
        self.function.setCurrentIndex(2)
        self.border.addItem('Little endian')
        self.border.addItem('Big endian')
        self.worder.addItem('Little endian')
        self.worder.addItem('Big endian')
        self.log.setFont(QFont('cascadia mono'))
        button.clicked.connect(self.Execute)
        self.setLayout(layout)

    def Execute(self):
        self.worker.setPaused(True)
        self.log.clear()
        deviceid=self.deviceid.value()
        address=self.address.value()#+self.args.offset
        count=self.count.value()
        response=None
        if self.border.currentIndex()==0:
            border='<'
        else:
            border='>'
        if self.worder.currentIndex()==0:
            worder='<'
        else:
            worder='>'
        try:
            if self.function.currentIndex()==0: response=self.client.read_coils(address,count,deviceid)
            if self.function.currentIndex()==1: response=self.client.read_discrete_inputs(address,count,deviceid)
            if self.function.currentIndex()==2: response=self.client.read_holding_registers(address,count,deviceid)
            if self.function.currentIndex()==3: response=self.client.read_input_registers(address,count,deviceid)
        except ModbusException as exc:
            self.log.addItem('Exception: '+str(exc))
            response=None
        if response!=None and (response.isError() or isinstance(response, ExceptionResponse)):
            self.log.addItem('Error: '+str(response))
            response=None
        if response!=None:
            # Do something
            if self.function.currentIndex()==0 or self.function.currentIndex()==1:
                for i in range(count):
                    self.log.addItem('Read address '+str(address)+': '+str(response.bits[i]))
                    address+=1
            if self.function.currentIndex()==2 or self.function.currentIndex()==3:
                decoder = BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=border, wordorder=worder)
                for register in response.registers:
                    self.log.addItem('Read address '+str(address)+': '+str(decoder.decode_16bit_uint()))
                    address+=1


        self.worker.setPaused(False)


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
        self.tablewidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablewidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablewidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablewidget.cellDoubleClicked.connect(self.doubleClicked)
        layout=QVBoxLayout()
        layout.addWidget(self.tablewidget,1)
        self.setLayout(layout)
        Utilities.setMargins(layout)
        self.datablock=datablock
        self.worker=worker

        # Populate table
        registers=worker.client.profile['datablocks'][datablock]
        self.table=[]
        for register in registers:
            row=[]
            row.append(registers[register]['dsc'])
            row.append(registers[register]['dtype'])
            row.append(registers[register]['rtype'].upper())
            row.append(register)
            row.append('')
            self.table.append(row)
        self.tablewidget.setColumnCount(5)
        self.tablewidget.setRowCount(len(self.table))
        self.tablewidget.setHorizontalHeaderItem(0,QTableWidgetItem('Description'))
        self.tablewidget.setHorizontalHeaderItem(1,QTableWidgetItem('Type'))
        self.tablewidget.setHorizontalHeaderItem(2,QTableWidgetItem('Access'))
        self.tablewidget.setHorizontalHeaderItem(3,QTableWidgetItem('Address'))
        self.tablewidget.setHorizontalHeaderItem(4,QTableWidgetItem('Value'))
        for i in range(len(self.table)):
            for j in range(len(self.table[i])):
                self.tablewidget.setItem(i,j,QTableWidgetItem(str(self.table[i][j])))

    ##\brief Update read/write value
    # \param datablock Datablock to update
    # \param address Register address that has changed
    # \param value New register value
    def update(self,datablock,address,value):
        for j in range(len(self.table)):
            if self.table[j][3]==str(address):
                self.tablewidget.setItem(j,4,QTableWidgetItem(str(value)))
                break

    ##\brief Event handler for double-clicks. Opens a dialog to write a register value
    # \param row The clicked row
    # \param column The clicked column (Not used)
    def doubleClicked(self,row,column):
        address=self.table[row][3]
        register=self.worker.client.profile['datablocks'][self.datablock][address]
        if register['rtype'].upper()=='R':
            resp=QMessageBox.question(self,'Confirmation','This value is marked read-only.\n\nDo you want to try overwriting it anyway?')
            if resp==QMessageBox.StandardButton.No: return

        dialog=SetValue('Write register',register)
        if dialog.exec_()!=0:
            register['value']=dialog.value
            self.worker.write(self.datablock,address,dialog.value)

##\class ClientUI
# \brief Main Application class
class ClientUI(QMainWindow):
    ##\brief Loads components and sets layout
    # \param args Parsed commandline arguments
    # \param parent Parent object
    def __init__(self,args,aboutstring):
        super(ClientUI,self).__init__(None)

        # Try to connect with dialog
        self.aboutstring=aboutstring
        self.client=None
        self.conframe=ConFrame(args)
        self.conframe.showMessagebox(True)
        while(True):
            if Connect(args,'MODBUS Client Options').exec_()!=0:
                self.client=ClientObject(args)
                if self.client.connect(): break
            else:
                logging.error('User aborted')
                sys.exit()
        self.worker=ClientWorker(self.client)
        self.worker.addReadCallback(self.update)
        self.worker.addWriteCallback(self.update)
        self.conframe.showMessagebox(False)
        self.conframe.clear()
        for line in aboutstring.split('\n'):
            self.conframe.addText(line)
        self.conframe.addText('')
        for line in App.reportConfig(args).split('\n'):
            self.conframe.addText(line)

        # Prepare update mechanism
        self.lock=threading.Lock()
        self.updates=[]

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
        conitem=StandardItem('Console')
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('di')))
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('co')))
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('hr')))
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('ir')))
        rootnode.appendRow(StandardItem('Custom request'))
        rootnode.appendRow(StandardItem('Device ID'))
        rootnode.appendRow(StandardItem('Logging'))
        rootnode.appendRow(conitem)

        # Wrap up treeview
        self.treeview.setModel(treemodel)
        self.treeview.expandAll()
        self.treeview.clicked.connect(self.treeviewClick)
        index=treemodel.indexFromItem(conitem)
        self.treeview.setCurrentIndex(index)

        # Load frames for registers
        self.table_di=ClientTableFrame(self.worker,'di')
        self.table_co=ClientTableFrame(self.worker,'co')
        self.table_hr=ClientTableFrame(self.worker,'hr')
        self.table_ir=ClientTableFrame(self.worker,'ir')
        self.customframe=CustomClientFrame(self.worker)
        self.deviceidframe=DeviceIdFrame(self.worker)
        self.table_di.setVisible(False)
        self.table_co.setVisible(False)
        self.table_hr.setVisible(False)
        self.table_ir.setVisible(False)
        self.customframe.setVisible(False)
        self.deviceidframe.setVisible(False)
        self.worker.start()

        # Load frame for logging
        self.logging=CSVLogger(self.client.profile)
        self.logging.setVisible(False)
        self.worker.addCompletedCallback(self.logging.logItems)

        # Create menubar
        self.createMenubar()

        # Use a timer to process data from the queue
        self.timer=QTimer()
        self.timer.timeout.connect(self.process)
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
        layout.addWidget(self.customframe)
        layout.addWidget(self.deviceidframe)
        layout.addWidget(self.logging)
        widget.setLayout(layout)
        scrollarea.setWidgetResizable(True)
        scrollarea.setWidget(widget)
        splitter=QSplitter(Qt.Horizontal)
        splitter.addWidget(self.treeview)
        splitter.addWidget(scrollarea)
        splitter.setSizes([200,500])
        self.setCentralWidget(splitter)
        self.setWindowTitle(App.getTitle('Client'))
        self.resize(800,600)
        self.showMaximized()
        logging.debug('Loaded GUI components')

    ##\brief Stop background processes upon terminating the application
    # \param event Not used
    def closeEvent(self, event):
        self.timer.stop()
        logging.info('Shutting down connection')
        if self.worker: self.worker.close()
        if self.client: self.client.close()
        super().close()

    ##\brief Respond to user clicking on the treeview
    # \param Value The clicked item
    def treeviewClick(self,Value):
        title=Value.data()
        self.table_di.setVisible(title==Utilities.getDatablockName('di'))
        self.table_co.setVisible(title==Utilities.getDatablockName('co'))
        self.table_hr.setVisible(title==Utilities.getDatablockName('hr'))
        self.table_ir.setVisible(title==Utilities.getDatablockName('ir'))
        self.customframe.setVisible(title=='Custom request')
        self.deviceidframe.setVisible(title=='Device ID')
        self.logging.setVisible(title=='Logging')
        self.conframe.setVisible(title=='Console')

    ##\brief Callback to register updated values from client
    # \param datablock Type of data to update
    # \param address Regisster address
    # \param value New value
    #
    # UI is only updated from Process() as that runs in UI thread
    def update(self,datablock,address,value):
        with self.lock:
            self.updates.append([datablock,address,value])

    ##\brief Timer event to update status and tranceivers in UI thread
    def process(self):
        # Update UI
        with self.lock:
            for update in self.updates:
                if update[0]=='di': self.table_di.update(update[0],update[1],update[2])
                if update[0]=='co': self.table_co.update(update[0],update[1],update[2])
                if update[0]=='hr': self.table_hr.update(update[0],update[1],update[2])
                if update[0]=='ir': self.table_ir.update(update[0],update[1],update[2])
                self.logging.update(update[0],update[1],update[2])

        # Update status bar
        icount,rcount,wcount,duration,iprg,rprg=self.worker.getStatus()
        self.status_rcount.setText('Reads: %d' % rcount)
        self.status_wcount.setText('Writes: %d' % wcount)
        self.status_queue.setText('Queue: %d items' % icount)
        self.status_duration.setText('Tr: %.3fms' % round(duration*1000,3))
        interval=self.worker.getInterval()
        if interval==None:
            self.status_int_progress.setValue(iprg)
            self.status_int_progress.setFormat('Automatic polling disabled')
        elif interval==0:
            self.status_int_progress.setValue(iprg)
            self.status_int_progress.setFormat('Continous polling')
        else:
            self.status_int_progress.setValue(iprg)
            self.status_int_progress.setFormat('Waiting for next read cycle '+str(iprg)+'%')
        if rprg:
            self.status_read_progress.setValue(rprg)
            self.status_read_progress.setFormat('Executing read cycle '+str(rprg)+'%')
        else:
            self.status_read_progress.setValue(rprg)
            self.status_read_progress.setFormat('Read cycle completed')

    ##\brief Creates menu bar
    def createMenubar(self):
        # Create menu actions
        #saveprofile=lambda x: self.SaveTextToFile('Device Configuration','devcfg',x)
        action_saveprofile=QAction('Save profile',self)
        action_saveprofile.setStatusTip('Save current profile to file')
        action_saveprofile.triggered.connect(lambda: Utilities.saveProfile(self.client.profile,self.getFilename('Profile','json')))
        action_exit=QAction('Exit',self)
        action_exit.triggered.connect(lambda: self.close())
        action_setinterval_0s=QAction('Continously',self,checkable=True,checked=False)
        action_setinterval_0s.setStatusTip('Poll continously')
        action_setinterval_0s.triggered.connect(lambda: self.worker.setInterval(0))
        action_setinterval_1s=QAction('1 second',self,checkable=True,checked=False)
        action_setinterval_1s.setStatusTip('Set polling interval to 1 second')
        action_setinterval_1s.triggered.connect(lambda: self.worker.setInterval(1))
        action_setinterval_15s=QAction('15 seconds',self,checkable=True,checked=False)
        action_setinterval_15s.setStatusTip('Set polling interval to 15 seconds')
        action_setinterval_15s.triggered.connect(lambda: self.worker.setInterval(15))
        action_setinterval_30s=QAction('30 seconds',self,checkable=True,checked=False)
        action_setinterval_30s.setStatusTip('Set polling interval to 30 seconds')
        action_setinterval_30s.triggered.connect(lambda: self.worker.setInterval(30))
        action_setinterval_1m=QAction('1 minute',self,checkable=True,checked=True)
        action_setinterval_1m.setStatusTip('Set polling interval to 1 minute')
        action_setinterval_1m.triggered.connect(lambda: self.worker.setInterval(60))
        action_setinterval_5m=QAction('5 minutes',self,checkable=True,checked=False)
        action_setinterval_5m.setStatusTip('Set polling interval to 5 minutes')
        action_setinterval_5m.triggered.connect(lambda: self.worker.setInterval(60*5))
        action_setinterval_15m=QAction('15 minutes',self,checkable=True,checked=False)
        action_setinterval_15m.setStatusTip('Set polling interval to 15 minutes')
        action_setinterval_15m.triggered.connect(lambda: self.worker.setInterval(60*15))
        action_setinterval_30m=QAction('30 minutes',self,checkable=True,checked=False)
        action_setinterval_30m.setStatusTip('Set polling interval to 30 minutes')
        action_setinterval_30m.triggered.connect(lambda: self.worker.setInterval(60*30))
        action_setinterval_1h=QAction('1 hour',self,checkable=True,checked=False)
        action_setinterval_1h.setStatusTip('Set polling interval to 1 hour')
        action_setinterval_1h.triggered.connect(lambda: self.worker.setInterval(3600))
        action_setinterval_3h=QAction('3 hours',self,checkable=True,checked=False)
        action_setinterval_3h.setStatusTip('Set polling interval to 3 hours')
        action_setinterval_3h.triggered.connect(lambda: self.worker.setInterval(3600*3))
        action_setinterval_6h=QAction('6 hours',self,checkable=True,checked=False)
        action_setinterval_6h.setStatusTip('Set polling interval to 6 hours')
        action_setinterval_6h.triggered.connect(lambda: self.worker.setInterval(3600*6))
        action_setinterval_12h=QAction('12 hours',self,checkable=True,checked=False)
        action_setinterval_12h.setStatusTip('Set polling interval to 12 hours')
        action_setinterval_12h.triggered.connect(lambda: self.worker.setInterval(3600*12))
        action_setinterval_24h=QAction('24 hours',self,checkable=True,checked=False)
        action_setinterval_24h.setStatusTip('Set polling interval to 24 hours')
        action_setinterval_24h.triggered.connect(lambda: self.worker.setInterval(3600*24))
        action_setinterval_none=QAction('Disable',self,checkable=True,checked=False)
        action_setinterval_none.setStatusTip('Disable automatic polling')
        action_setinterval_none.triggered.connect(lambda: self.worker.setInterval(None))
        action_setinterval_now=QAction('Read now',self)
        action_setinterval_now.setStatusTip('Trigger immidiate read-cycle')
        action_setinterval_now.triggered.connect(lambda: self.worker.trigger())
        action_setinterval=QActionGroup(self)
        action_setinterval.addAction(action_setinterval_0s)
        action_setinterval.addAction(action_setinterval_1s)
        action_setinterval.addAction(action_setinterval_15s)
        action_setinterval.addAction(action_setinterval_30s)
        action_setinterval.addAction(action_setinterval_1m)
        action_setinterval.addAction(action_setinterval_5m)
        action_setinterval.addAction(action_setinterval_15m)
        action_setinterval.addAction(action_setinterval_30m)
        action_setinterval.addAction(action_setinterval_1h)
        action_setinterval.addAction(action_setinterval_3h)
        action_setinterval.addAction(action_setinterval_6h)
        action_setinterval.addAction(action_setinterval_12h)
        action_setinterval.addAction(action_setinterval_24h)
        action_setinterval.addAction(action_setinterval_none)
        action_about=QAction('About '+App.getTitle('Client'),self)
        action_about.triggered.connect(lambda: QMessageBox.about(self,'About','\t\t\t\t\t\t\t\t\t'+self.aboutstring+'\n\n'))

        # Creating menus
        menubar = QMenuBar(self)
        filemenu = QMenu("&File", self)
        filemenu.addAction(action_saveprofile)
        filemenu.addSeparator()
        filemenu.addAction(action_exit)
        intmenu = QMenu("&Interval", self)
        intmenu.addAction(action_setinterval_0s)
        intmenu.addAction(action_setinterval_1s)
        intmenu.addAction(action_setinterval_15s)
        intmenu.addAction(action_setinterval_30s)
        intmenu.addAction(action_setinterval_1m)
        intmenu.addAction(action_setinterval_5m)
        intmenu.addAction(action_setinterval_15m)
        intmenu.addAction(action_setinterval_30m)
        intmenu.addAction(action_setinterval_1h)
        intmenu.addAction(action_setinterval_3h)
        intmenu.addAction(action_setinterval_6h)
        intmenu.addAction(action_setinterval_12h)
        intmenu.addAction(action_setinterval_24h)
        intmenu.addAction(action_setinterval_none)
        intmenu.addSeparator()
        intmenu.addAction(action_setinterval_now)
        helpmenu = QMenu("&Help", self)
        helpmenu.addAction(action_about)
        menubar.addMenu(filemenu)
        menubar.addMenu(intmenu)
        menubar.addMenu(helpmenu)
        self.setMenuBar(menubar)

    ##\brief Get filename from user input
    # \param Desc Textual description of output file
    # \param Ext File extension to save as
    # \return filename
    def getFilename(self,Desc,Ext):
        options = QFileDialog.Options()
        title='Save '+Desc
        default=Desc+'.'+Ext
        filter=Desc+'(*.'+Ext+');;All Files(*.*)'
        filename, _ = QFileDialog.getSaveFileName(self,title,default,filter,options=options)
        return filename

if __name__ == "__main__":
    aboutstring=App.getAbout('client','GUI client for MODBUS Testing')
    app=QApplication(sys.argv)
    window=ClientUI(Loader(gui=True).clientargs,aboutstring)
    app.exec()
