##\package components
# \brief Common GUI components
#
# Vegard Fiksdal (C) 2024
#

# Import QT framework
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QComboBox, QLabel, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QMessageBox, QFrame, QFileDialog
from PyQt5.Qt import QStandardItem
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QTimer
from pymodbus import pymodbus_apply_logging_config
import datetime
import serial.tools.list_ports
from common import *

##\class ConFrame
# \brief Frame to display realtime log output
class ConFrame(QFrame):
    ##\brief Constructor sets up frame layout
    # \param args Parsed commandline arguments
    def __init__(self,args):
        super().__init__()
        self.handler=LogHandler()
        self.listbox=QListWidget()
        self.listbox.setFont(QFont('cascadia mono'))
        self.dropdown=QComboBox()
        self.clearbutton=QPushButton('Clear logs')
        self.clearbutton.clicked.connect(self.Clear)
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
        Utils.setMargins(layout)

        # Use a timer to process data from the queue
        self.timer=QTimer()
        self.timer.timeout.connect(self.Update)
        self.timer.start(250)


    ##\brief Called when loglevel has changed
    # \param index New loglevel
    def currentIndexChanged(self,index):
        levelname=self.dropdown.itemText(index)
        level=logging._nameToLevel[levelname]
        pymodbus_apply_logging_config(levelname)
        logging.basicConfig(level=level,handlers=[self.handler])

    ##\brief Clear existing log
    def Clear(self):
        self.messages=[]
        self.listbox.clear()

    ##\brief Manually adds a text string
    # \param text Text string to add
    def AddText(self,text):
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
    def Update(self):
        if self.handler:
            messages=self.handler.messages
            self.handler.messages=[]
            for message in messages:
                if self.msgbox and (message.levelno==logging.ERROR or message.levelno==logging.CRITICAL):
                    QMessageBox.critical(self,message.module,str(message.msg))
                s='%s  %-*s %s' % (datetime.datetime.now().strftime('%c'),8,message.levelname,message.msg)
                self.listbox.addItem(s)
            if len(messages):
                self.listbox.scrollToBottom()

##\class LogHandler
# \brief Custom logging handler for GUI output
class LogHandler(logging.Handler):
    ##\brief Initializes handler
    def __init__(self):
        self.messages=[]
        super().__init__()

    def emit(self, record):
        self.messages.append(record)


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
    # \param register Dictionary describing the register to set
    def __init__(self,register):
        super(SetValue,self).__init__(None)
        self.setWindowTitle("Change modbus register")
        self.register=register
        layout=QVBoxLayout()
        self.valueedit=QLineEdit(str(register['value']))
        self.buttons=QDialogButtonBox(self)
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttons.accepted.connect(self.Set)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(QLabel('Enter new register value of type '+register['dtype']))
        layout.addWidget(self.valueedit)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    ##\brief Validates the user input
    def Set(self):
        try:
            self.value=Utils.castRegister(self.register,self.valueedit.text())
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
    # \param server True for server connection, False for client
    def __init__(self,args):
        super(Connect,self).__init__(None)
        self.setWindowTitle("MODBUS Connection")
        #self.resize(500,200)
        self.args=args
        self.profilelist=QComboBox()
        self.commlist=QComboBox()
        self.framerlist=QComboBox()
        self.slaveidedit=QLineEdit(str(args.slaveid))
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
        vlayout=QVBoxLayout()
        vlayout.addWidget(QLabel('MODBUS profile'))
        vlayout.addWidget(self.profilelist)
        vlayout.addWidget(QLabel('Communication interface'))
        vlayout.addWidget(self.commlist)
        vlayout.addWidget(QLabel('MODBUS framer'))
        vlayout.addWidget(self.framerlist)
        vlayout.addWidget(QLabel('Slave ID'))
        vlayout.addWidget(self.slaveidedit)
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
        self.buttons.accepted.connect(self.Open)
        self.buttons.rejected.connect(self.reject)

        # Enumerate profiles
        default=0
        self.profiles=Utils.listProfiles()
        for profile in self.profiles:
            if os.path.abspath(args.profile).upper()==profile.upper(): default=self.profilelist.count()
            self.profilelist.addItem(os.path.basename(profile)[:-5])
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
        self.setDefault(self.paritylist,Utils.getParityName(args.parity))


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
    def Open(self):
        # Try to connect
        try:
            self.args.profile = self.profiles[self.profilelist.currentIndex()]
            self.args.comm = self.commlist.currentText().lower()
            self.args.framer = self.framerlist.currentText().lower()
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
            self.args.slaveid=int(self.slaveidedit.text())
            super().accept()
        except Exception as error:
            logging.error(str(error))
        except:
            logging.error('An unknown error occurred')
