##\package components
# \brief Common GUI components
#
# Vegard Fiksdal (C) 2024
#

# Import QT framework
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QComboBox, QLabel, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, QFileDialog, QTableWidget, QTableWidgetItem
from PyQt5.Qt import QStandardItem, QHeaderView, QAbstractItemView
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QTimer
from pymodbus import pymodbus_apply_logging_config
import datetime,threading
import serial.tools.list_ports
from common import *

##\class BrowseBox
# \brief Class to display a label + edit control + browse button to set paths
class BrowseBox(QFrame):
    def __init__(self,label,text=os.getcwd(),locked=False):
        super().__init__()
        self.label=QLabel(label)
        self.edit=QLineEdit(str(text))
        self.button=QPushButton('...')
        self.edit.setEnabled(not locked)
        self.button.setEnabled(not locked)
        self.button.clicked.connect(self.browse)
        layout=QHBoxLayout()
        ilayout=QHBoxLayout()
        ilayout.addWidget(self.edit,1)
        ilayout.addWidget(self.button)
        layout.addWidget(self.label,1)
        layout.addLayout(ilayout,1)
        Utilities.setMargins(layout)
        self.setLayout(layout)

    ##\brief Opens a file dialog to set the path visually
    def browse(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if len(folder): self.edit.setText(str(folder))

    ##\brief Changes the value
    # \param Text New value as a string
    def setValue(self,Value):
        self.edit.setText(str(Value))

    ##\brief Get current value
    # \return String describing a path. Not checked in any way.
    def getValue(self):
        return self.edit.text()

##\class ConFrame
# \brief Frame to display realtime log output
class ConFrame(QFrame):
    ##\brief Constructor sets up frame layout
    # \param args Parsed commandline arguments
    def __init__(self,args):
        super().__init__()
        self.listbox=QListWidget()
        self.listbox.setFont(QFont('cascadia mono'))
        self.dropdown=QComboBox()
        self.clearbutton=QPushButton('Clear logs')
        self.clearbutton.clicked.connect(self.clear)
        self.savebutton=QPushButton('Save log to file')
        self.savebutton.clicked.connect(self.savelog)
        self.messages=[]
        self.msgbox=False

        # Manage loglevels
        levels=['CRITICAL','ERROR','WARNING','INFO','DEBUG']
        level=3
        for i in range(len(levels)):
            self.dropdown.addItem(levels[i])
            if args.log.upper()==levels[i]: level=i
        self.dropdown.currentIndexChanged.connect(self.currentIndexChanged)
        self.dropdown.setCurrentIndex(level)

        # Add any controls to the layout
        layout=QVBoxLayout()
        layout.addWidget(self.listbox,1)
        layout.addWidget(self.dropdown)
        layout.addWidget(self.clearbutton)
        layout.addWidget(self.savebutton)
        self.setLayout(layout)
        Utilities.setMargins(layout)

        # Assign ourselves as log output
        LogHandler.output=self

        # Use a timer to process data from the queue
        self.timer=QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(250)


    ##\brief Called when loglevel has changed
    # \param index New loglevel
    def currentIndexChanged(self,index):
        levelname=self.dropdown.itemText(index)
        level=logging._nameToLevel[levelname]
        LogHandler.level=level

    ##\brief Clear existing log
    def clear(self):
        self.messages=[]
        self.listbox.clear()

    ##\brief Process messages from logger
    def processLog(self,message):
        self.messages.append(message)

    ##\brief Manually adds a text string
    # \param text Text string to add
    def addText(self,text):
        self.listbox.addItem(text)

    ##\brief Saves log output to file
    def savelog(self):
        text=''
        for message in self.messages:
            text+=message+'\n'
        filename, _ = QFileDialog.getSaveFileName(self,'Save process log','mbserver.log','Log files(*.log);;All Files(*.*)',options=QFileDialog.Options())
        if filename:
            with open(filename, 'w') as f:
                f.write(text)
                f.close()

    ##\brief Show errors in a messagebox
    # \param show True to display messagebox for error messages
    #
    # This is useful when connecting
    def showMessagebox(self,show):
        self.msgbox=show

    ##\brief Updates GUI with added messages
    def update(self):
        messages=self.messages
        self.messages=[]
        for message in messages:
            if self.msgbox and (message.levelno==logging.ERROR or message.levelno==logging.CRITICAL):
                QMessageBox.critical(self,message.module,str(message.msg))
            s='%s  %-*s %s' % (datetime.datetime.now().strftime('%c'),8,message.levelname,message.msg)
            self.listbox.addItem(s)
        if len(messages):
            self.listbox.scrollToBottom()

##\class StandardItem
# \brief Define how a standard treeview item should look like
class StandardItem(QStandardItem):
    ##\brief Configures StandardItem
    # \param txt Text to display
    # \param font_size Size of font
    # \param set_bold Wether to have bold font
    # \param color Color of the text
    def __init__(self, txt='', font_size=12, set_bold=False, color=QColor(0,0,0)):
        super().__init__()
        fnt = QFont('Open Sans', font_size)
        fnt.setBold(set_bold)
        self.setEditable(False)
        self.setForeground(color)
        self.setFont(fnt)
        self.setText(txt)

##\class SetValue
# \brief Custom dialog to set a value
class SetValue(QDialog):
    ##\brief Initializes the dialog
    # \param title Dialog title to describe action
    # \param register Dictionary describing the register to set
    def __init__(self,title,register):
        super(SetValue,self).__init__(None)
        self.setWindowTitle(title)
        self.register=register
        layout=QVBoxLayout()
        self.valueedit=QLineEdit(str(register['value']))
        self.buttons=QDialogButtonBox(self)
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttons.accepted.connect(self.set)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(QLabel('Enter new register value of type '+register['dtype']))
        layout.addWidget(self.valueedit)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    ##\brief Validates the user input
    def set(self):
        try:
            self.value=Registers.castRegister(self.register,self.valueedit.text())
            super().accept()
        except Exception as error:
            QMessageBox.critical(self,'Error',str(error))
        except:
            QMessageBox.critical(self,'Error','An unknown error occurred')

##\class Connect
# \brief Window to display connection options to the user
class Connect(QDialog):
    ##\brief Initializes the dialog
    # \param args Parsed commandline arguments
    # \param title Dialog title to be displayed
    # \param server True for server connection, False for client
    def __init__(self,args,title,hideprofile=False):
        super(Connect,self).__init__(None)
        self.setWindowTitle(title)
        self.resize(500,200)
        self.args=args
        self.profilelabel=QLabel('MODBUS profile')
        self.profilelist=QComboBox()
        self.commlist=QComboBox()
        self.framerlist=QComboBox()
        self.deviceidedit=QLineEdit(str(args.deviceid))
        self.hostlabel=QLabel('Host address')
        self.hostedit=QLineEdit(str(args.host))
        self.nportlabel=QLabel('Network port')
        self.nportedit=QLineEdit(str(args.port))
        self.sportlabel=QLabel('Serial port')
        self.sportlist=QComboBox()
        self.baudlabel=QLabel('Baudrate')
        self.baudlist=QComboBox()
        self.paritylabel=QLabel('Parity')
        self.paritylist=QComboBox()
        self.flowlabel=QLabel('Flowcontrol')
        self.flowlist=QComboBox()
        self.buttons=QDialogButtonBox(self)
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        hlayout=QHBoxLayout()
        self.browse=QPushButton('...')
        self.browse.clicked.connect(self.Browse)
        vlayout=QVBoxLayout()
        vlayout.addWidget(self.profilelabel)
        hlayout.addWidget(self.profilelist,1)
        hlayout.addWidget(self.browse)
        vlayout.addLayout(hlayout)
        vlayout.addWidget(QLabel('Communication interface'))
        vlayout.addWidget(self.commlist)
        vlayout.addWidget(QLabel('MODBUS framer'))
        vlayout.addWidget(self.framerlist)
        vlayout.addWidget(QLabel('Device ID'))
        vlayout.addWidget(self.deviceidedit)
        vlayout.addWidget(self.hostlabel)
        vlayout.addWidget(self.hostedit)
        vlayout.addWidget(self.nportlabel)
        vlayout.addWidget(self.nportedit)
        vlayout.addWidget(self.sportlabel)
        vlayout.addWidget(self.sportlist)
        vlayout.addWidget(self.baudlabel)
        vlayout.addWidget(self.baudlist)
        vlayout.addWidget(self.paritylabel)
        vlayout.addWidget(self.paritylist)
        vlayout.addWidget(self.flowlabel)
        vlayout.addWidget(self.flowlist)
        vlayout.addWidget(QLabel(''),1)
        vlayout.addWidget(self.buttons)
        self.setLayout(vlayout)
        self.buttons.accepted.connect(self.open)
        self.buttons.rejected.connect(self.reject)

        # Optionally hide profile selection
        if hideprofile:
            self.profilelabel.setVisible(False)
            self.profilelist.setVisible(False)

        # Enumerate profiles
        default=0
        self.profiles=Profiles.listProfiles(args)
        for profile in self.profiles:
            if os.path.basename(args.profile).upper()==profile[1].upper(): default=self.profilelist.count()
            self.profilelist.addItem(os.path.basename(profile[1])[:-5])
        self.profilelist.setCurrentIndex(default)

        # Enumerate ports
        default=0
        ports=serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            logging.debug("Enumerating {}={} [{}]".format(port,desc,hwid))
            if args.serial.upper()==port.upper(): default=self.sportlist.count()
            self.sportlist.addItem("{}:\t{}".format(port,desc))
        self.sportlist.setCurrentIndex(default)

        # Populate lists
        self.commlist.addItem('Serial')
        self.commlist.addItem('TCP')
        self.commlist.addItem('UDP')
        self.baudlist.addItem('9600')
        self.baudlist.addItem('115200')
        self.baudlist.addItem('230400')
        self.paritylist.addItem('None')
        self.paritylist.addItem('Odd')
        self.paritylist.addItem('Even')
        self.flowlist.addItem('None')
        self.flowlist.addItem('XON/XOFF')
        self.flowlist.addItem('RTS/CTS')
        self.flowlist.addItem('DSR/DTR')

        # Set up dialog
        self.show()
        self.commlist.currentIndexChanged.connect(self.commChanged)
        self.commChanged(self.commlist.currentIndex())
        self.setDefault(self.commlist,args.comm)
        self.setDefault(self.framerlist,args.framer)
        self.setDefault(self.baudlist,args.baudrate)
        self.setDefault(self.paritylist,Utilities.getParityName(args.parity))

    def Browse(self):
        filename, _ = QFileDialog.getOpenFileName(self,'Load profile','','Profile files(*.json);;All Files(*.*)',options=QFileDialog.Options())
        if len(filename) and os.path.exists(filename):
            self.profilelist.addItem(filename)
            self.profilelist.setCurrentIndex(self.profilelist.count()-1)

    ##\brief Set dropdown selection to a default value
    # \param argument Desired default value
    def setDefault(self,dropdown,argument):
        for i in range(dropdown.count()):
            if dropdown.itemText(i).upper()==str(argument).upper():
                dropdown.setCurrentIndex(i)

    ##\brief Rearranges the dialog according the users choice of interface
    # \param index Index om the selected communication interface
    def commChanged(self,index):
        # Rearrange dialog
        framer=self.framerlist.currentText()
        self.framerlist.clear()
        is_serial=(self.commlist.itemText(index)=='Serial')
        if not is_serial: self.framerlist.addItem('Socket')
        self.framerlist.addItem('RTU')
        self.framerlist.addItem('ASCII')
        self.hostlabel.setVisible(not is_serial)
        self.hostedit.setVisible(not is_serial)
        self.nportlabel.setVisible(not is_serial)
        self.nportedit.setVisible(not is_serial)
        self.sportlabel.setVisible(is_serial)
        self.sportlist.setVisible(is_serial)
        self.baudlabel.setVisible(is_serial)
        self.baudlist.setVisible(is_serial)
        self.paritylabel.setVisible(is_serial)
        self.paritylist.setVisible(is_serial)
        self.flowlabel.setVisible(is_serial)
        self.flowlist.setVisible(is_serial)

        # Change back to original framer if applicable
        self.setDefault(self.framerlist,framer)

    ##\brief Attempt to start a connection with the current selection
    def open(self):
        # Try to connect
        try:
            self.args.comm = self.commlist.currentText().lower()
            self.args.framer = self.framerlist.currentText().lower()
            if self.profilelist.currentIndex()<len(self.profiles):
                profiles=self.profiles[self.profilelist.currentIndex()]
                self.args.profile = profiles[0]+profiles[1]
            else:
                self.args.profile=self.profilelist.itemText(self.profilelist.currentIndex())
            if not os.path.exists(self.args.profile):
                logging.error('Invalid profile: '+str(self.args.profile))
                return
            if self.args.comm == 'serial':
                # Parse flowcontrol
                self.args.xonxoff=0
                self.args.rtscts=0
                self.args.dsrdtr=0
                if self.flowlist.currentText()=='XON/XOFF': self.args.xonxoff=1
                if self.flowlist.currentText()=='RTS/CTS':  self.args.rtscts=1
                if self.flowlist.currentText()=='DSR/DTR':  self.args.dsrdtr=1

                # Parse serial port name
                port=self.sportlist.currentText()
                if port.find(':')>0: port=port[:port.find(':')]
                self.args.serial=port

                # Collect other data
                self.args.baudrate=int(self.baudlist.currentText())
                self.args.parity=self.paritylist.currentText()[0]
            else:
                self.args.host=self.hostedit.text()
                self.args.port=self.nportedit.text()
            self.args.deviceid=int(self.deviceidedit.text())
            super().accept()
        except Exception as error:
            logging.error(str(error))
        except:
            logging.error('An unknown error occurred')

class CSVLogger(QFrame):
    def __init__(self,profile):
        super(CSVLogger,self).__init__(None)
        self.tablewidget=QTableWidget()
        self.tablewidget.verticalHeader().setVisible(False)
        self.tablewidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablewidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablewidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.startbutton=QPushButton('Start logging')
        self.browse=BrowseBox('Logging directory')
        layout=QVBoxLayout()
        layout.addWidget(self.tablewidget,1)
        layout.addWidget(self.browse)
        layout.addWidget(self.startbutton)
        self.setLayout(layout)
        Utilities.setMargins(layout)
        self.startbutton.clicked.connect(self.startStop)
        self.fd=None

        # Populate table
        self.profile=profile
        self.table=[]
        for datablock in profile['datablocks']:
            datatype=Utilities.getDatablockName(datablock)
            for register in profile['datablocks'][datablock]:
                registers=profile['datablocks'][datablock]
                column=[]
                column.append(datatype)
                column.append(registers[register]['dsc'])
                column.append(register)
                column.append(registers[register]['value'])
                self.table.append(column)
        self.tablewidget.setColumnCount(4)
        self.tablewidget.setRowCount(len(self.table))
        self.tablewidget.setHorizontalHeaderItem(0,QTableWidgetItem('Datablock'))
        self.tablewidget.setHorizontalHeaderItem(1,QTableWidgetItem('Description'))
        self.tablewidget.setHorizontalHeaderItem(2,QTableWidgetItem('Address'))
        self.tablewidget.setHorizontalHeaderItem(3,QTableWidgetItem('Value'))
        for i in range(len(self.table)):
            for j in range(len(self.table[i])):
                self.tablewidget.setItem(i,j,QTableWidgetItem(str(self.table[i][j])))

    ##\brief Start or stops logging to disk
    def startStop(self):
        start=self.tablewidget.isEnabled()
        if start:
            # Check items to log
            items=self.tablewidget.selectedItems()
            cols=self.tablewidget.columnCount()
            if len(items)==0:
                QMessageBox.critical(self,'Error','No items selected for logging!')
                return

            # Open file
            path=self.browse.getValue()
            filename=path+'/'+datetime.datetime.now().strftime('MBTester - %Y%m%d %H%M%S')+'.csv'
            self.fd=open(filename,'w')
            if not self.fd:
                QMessageBox.critical(self,'Error','Could not write to '+path)
                return

            # Write header
            csv='Time'
            for i in range(0,len(items),cols):
                hdr=items[i+1].text()
                if hdr=='': hdr=items[i+cols-2].text()
                hdr.replace(',','_')
                csv+=','+items[i+1].text()
            self.fd.write(csv+'\n')
            self.startbutton.setText('Stop logging')
        else:
            # Close file
            if self.fd:
                self.fd.close()
                self.fd=None
            self.startbutton.setText('Stop logging')

        # Reset dialog
        self.tablewidget.setEnabled(not start)
        self.browse.setEnabled(not start)

    ##\brief Log current values to CSV file
    def logItems(self):
        if self.fd:
            items=self.tablewidget.selectedItems()
            cols=self.tablewidget.columnCount()
            csv=str(datetime.datetime.now())
            for i in range(0,len(items),cols):
                csv+=','+items[i+cols-1].text()
            self.fd.write(csv+'\n')
            self.fd.flush()

    ##\brief Update read/write value
    # \param address Register address that has changed
    # \param value New register value
    def update(self,datablock,address,value):
        datatype=Utilities.getDatablockName(datablock)
        for j in range(len(self.table)):
            if self.table[j][0]==datatype and self.table[j][2]==str(address):
                self.tablewidget.setItem(j,3,QTableWidgetItem(str(value)))
                break
