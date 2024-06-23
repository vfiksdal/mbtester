##\package mbtserver
# \brief MBTester Server using Qt
#
# Vegard Fiksdal (C) 2024
#

# Import QT modules
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar, QSplitter, QTreeView, QStatusBar, QScrollArea, QMenuBar, QMenu, QAction
from PyQt5.Qt import QStandardItemModel
from PyQt5.QtCore import Qt, QTimer

# Import local modules
from components import *
from mbtserver import *


##\class ServerTableFrame
# \brief Table to hold and interact with a modbus register block
class ServerTableFrame(QFrame):
    ##\brief Constructor sets up frame layout
    # \param server Modbus server object (Fully connected)
    # \param datablock Name of datablock (di, co, hr or ir)
    def __init__(self,server,datablock):
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
        self.server=server
        self.updates=[]
        self.rcount=0
        self.wcount=0

        getattr(self.server,self.datablock).addWriteCallback(self.updateWrite)
        getattr(self.server,self.datablock).addReadCallback(self.updateRead)

        # Populate table
        registers=server.profile['datablocks'][datablock]
        self.table=[]
        for register in registers:
            column=[]
            column.append(registers[register]['dsc'])
            column.append(registers[register]['dtype'])
            column.append(registers[register]['rtype'].upper())
            column.append(register)
            column.append(registers[register]['value'])
            self.table.append(column)
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

    def getStatus(self):
        return len(self.table)-1,self.rcount,self.wcount

    ##\brief Update read/write value
    # \param address Register address that has changed
    # \param value New register value
    #
    # This method only tags the changed value. The actual UI will be updated later on
    # the main UI thread -- See UpdateUI().
    def updateWrite(self,datablock,address,value):
        self.updates.append([address,value])
        self.wcount+=1

    def updateRead(self,datablock,address,value):
        self.rcount+=1

    ##\brief Update UI controls
    #
    # This method updated the UI according to the register changes tracked by Update()
    def updateUI(self):
        updates=self.updates
        self.updates=[]
        for i in range(len(updates)):
            address=updates[i][0]
            value=updates[i][1]
            for j in range(len(self.table)):
                if self.table[j][3]==str(address):
                    register=self.server.profile['datablocks'][self.datablock][str(address)]
                    value=Registers.decodeRegister(register,value)
                    self.tablewidget.setItem(j,4,QTableWidgetItem(str(value)))
                    register['value']=value

    ##\brief Event handler for double-clicks. Opens a dialog to write a register value
    # \param row The clicked row
    # \param column The clicked column (Not used)
    def doubleClicked(self,row,column):
        address=self.table[row][3]
        register=self.server.profile['datablocks'][self.datablock][address]
        dialog=SetValue('Change register',register)
        if dialog.exec_()!=0:
            value=Registers.encodeRegister(register,dialog.value)
            getattr(self.server,self.datablock).setValues(int(address),value)

##\class ServerUI
# \brief Main Application class
class ServerUI(QMainWindow):
    ##\brief Loads components and sets layout
    # \param args Parsed commandline arguments
    # \param parent Parent object
    def __init__(self,args,parent=None):
        super(ServerUI,self).__init__(parent)

        # Try to connect with dialog
        self.server=None
        self.conframe=ConFrame(args)
        self.conframe.showMessagebox(True)
        while(True):
            if Connect(args).exec_()!=0:
                self.server=ServerObject(args)
                if self.server.startServer(): break
            else:
                logging.error('User aborted')
                sys.exit()
        self.conframe.showMessagebox(False)
        self.conframe.clear()
        for line in aboutstring.split('\n'):
            self.conframe.addText(line)
        self.conframe.addText('')
        for line in App.reportConfig(args).split('\n'):
            self.conframe.addText(line)

        # Add statusbar
        self.statusbar=QStatusBar()
        self.status_progress=QProgressBar()
        self.status_icount=QLineEdit()
        self.status_rcount=QLineEdit()
        self.status_wcount=QLineEdit()
        self.status_progress.setEnabled(False)
        self.status_icount.setEnabled(False)
        self.status_rcount.setEnabled(False)
        self.status_wcount.setEnabled(False)
        self.statusbar.addWidget(self.status_icount)
        self.statusbar.addWidget(self.status_rcount)
        self.statusbar.addWidget(self.status_wcount)
        self.statusbar.addWidget(self.status_progress,1)
        self.setStatusBar(self.statusbar)
        self.status_progress.setAlignment(Qt.AlignCenter)
        self.statusbar.setVisible(True)
        
        # Build treeview
        self.treeview=QTreeView()
        self.treeview.setHeaderHidden(True)
        treemodel=QStandardItemModel()
        rootnode=treemodel.invisibleRootItem()
        logitem=StandardItem('Console')
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('di')))
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('co')))
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('hr')))
        rootnode.appendRow(StandardItem(Utilities.getDatablockName('ir')))
        rootnode.appendRow(logitem)

        # Wrap up treeview
        self.treeview.setModel(treemodel)
        self.treeview.expandAll()
        self.treeview.clicked.connect(self.treeviewClick)
        index=treemodel.indexFromItem(logitem)
        self.treeview.setCurrentIndex(index)
        #self.treeview.setEnabled(False)

        # Load frames for registers
        self.table_di=ServerTableFrame(self.server,'di')
        self.table_co=ServerTableFrame(self.server,'co')
        self.table_hr=ServerTableFrame(self.server,'hr')
        self.table_ir=ServerTableFrame(self.server,'ir')
        self.table_di.setVisible(False)
        self.table_co.setVisible(False)
        self.table_hr.setVisible(False)
        self.table_ir.setVisible(False)

        # Create menubar
        self.createMenubar()

        # Use a timer to process data from the queue
        self.timer=QTimer()
        self.timer.timeout.connect(self.process)
        self.timer.start(100)

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
        if self.server: self.server.stopServer()
        super().close()

    ##\brief Respond to user clicking on the treeview
    # \param Value The clicked item
    def treeviewClick(self,Value):
        title=Value.data()
        self.table_di.setVisible(title==Utilities.getDatablockName('di'))
        self.table_co.setVisible(title==Utilities.getDatablockName('co'))
        self.table_hr.setVisible(title==Utilities.getDatablockName('hr'))
        self.table_ir.setVisible(title==Utilities.getDatablockName('ir'))
        self.conframe.setVisible(title=='Console')

    ##\brief Timer event to update status and tranceivers
    def process(self):
        # Update register lists
        self.table_di.updateUI()
        self.table_co.updateUI()
        self.table_hr.updateUI()
        self.table_ir.updateUI()

        # Update status
        icount_di,rcount_di,wcount_di=self.table_di.getStatus()
        icount_co,rcount_co,wcount_co=self.table_co.getStatus()
        icount_hr,rcount_hr,wcount_hr=self.table_hr.getStatus()
        icount_ir,rcount_ir,wcount_ir=self.table_ir.getStatus()
        icount=icount_di+icount_co+icount_hr+icount_ir
        rcount=rcount_di+rcount_co+rcount_hr+rcount_ir
        wcount=wcount_di+wcount_co+wcount_hr+wcount_ir
        self.status_icount.setText('Items: %d' % icount)
        self.status_rcount.setText('Reads: %d' % rcount)
        self.status_wcount.setText('Writes: %d' % wcount)

    ##\brief Creates menu bar
    def createMenubar(self):
        # Create menu actions
        action_saveprofile=QAction('Save profile',self)
        action_saveprofile.setStatusTip('Save current profile to file')
        action_saveprofile.triggered.connect(lambda: Profiles.saveProfile(self.server.profile,self.getFilename('Profile','json')))
        action_exit=QAction('Exit',self)
        action_exit.triggered.connect(lambda: self.close())
        action_about=QAction('About '+application,self)
        action_about.triggered.connect(lambda: QMessageBox.about(self,'About','\t\t\t\t\t\t\t\t\t'+aboutstring+'\n\n'))

        # Creating menus
        menubar = QMenuBar(self)
        filemenu = QMenu("&File", self)
        filemenu.addAction(action_saveprofile)
        filemenu.addSeparator()
        filemenu.addAction(action_exit)
        helpmenu = QMenu("&Help", self)
        helpmenu.addAction(action_about)
        menubar.addMenu(filemenu)
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


# Simple identification
aboutstring=App.getAbout('server','GUI server for MODBUS Testing')
application=App.getName()+' Server '+App.getVersion()
aboutstring=application+'\n'
aboutstring+='GUI server for MODBUS Testing\n'
aboutstring+='Vegard Fiksdal(C)2024'

# Load application window and start application
args=App.parseArguments(aboutstring)
app=QApplication(sys.argv)
window=ServerUI(args)
app.exec()
