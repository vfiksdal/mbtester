# MBTester
A suite of client's and server's to test and emulate MODBUS implementations. A MODBUS interface is defined in JSON and can be used to simulate both server and client ends of the communication. Leveraged by the pymodbus library it fully supports any RTU, ASCII and TCP/IP combinations you may need in your project.

# Installation
First install a python3 distribution of your choice, winpython works well for windows users, linux/mac users can use what ships with their OS.
Then you need to install some dependencies:

>python -m pip install pyserial pymodbus

Finally you can run the CLI server:
>python mbserver.py --profile Test_Simple.json

Alternatively you can run the QT GUI server, allowing you to monitor and and change registers on the fly:
>python mbtserver.py --profile Test_Simple.json

You may also want to run the client counterpart, letting you send and transmit registers back and forth:
>python mbtclient.py --profile Test_Simple.json

