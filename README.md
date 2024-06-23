# MBTester
A suite of client's and server's to test and emulate MODBUS implementations. A MODBUS interface is defined in JSON and can be used to simulate both server and client ends of the communication. Leveraged by the pymodbus library it fully supports any RTU, ASCII and TCP/IP combinations you may need in your project.

# Installation
First install a python3 distribution of your choice, winpython works well for windows users, linux/mac users can use what ships with their OS.
Then you need to install some dependencies:

>python -m pip install pyserial pymodbus

Finally you can run the CLI server:
>python mbtserver.py --profile Test_Simple.json

Now you can run the CLI client counterpart, downloading the dataset from the server:
>python mbtclient.py --profile Test_Simple.json

# Writing a MODBUS profile
Before you can use MBTester you need a modbus profile. This is a .json file which defines all the registers your device or integration needs. The simple test files in the repo has a set of holding registers as shown below. Each register has an address, a textual description, data type and value. You can also choose to define word-order, byte-order and read/write access for each register if you want to. Please check the other examples for reference.
![image](https://github.com/vfiksdal/mbtester/assets/51258725/27d9f067-4894-4012-aa87-4152d2e58b6c)

You can now load the profile in a CLI server.
>python mbtserver.py --profile Test_Simple.json

Alternatively, you can load it in mbtserver.py for a GUI server where you can monitor writes, change registers on the fly etc.
>python qmbtserver.py

![image](https://github.com/vfiksdal/mbtester/assets/51258725/3024a616-a2d7-44b3-a08d-8ff132bc94e2)

With the server running you can start a client. Choose the profile you wrote (Must be in the same folder) and the appropriate settings, and connect to the server. You can now monitor the registers in real-time or double-click one to write a new value.
>python qmbtclient.py

![image](https://github.com/vfiksdal/mbtester/assets/51258725/ef93e25a-78c5-40c4-839a-9deb1aca6e60)

# Using MBTester
The actual usage of this application depends upon what you want to accomplish with it. But generally speaking you first want to write a profile to define your interface, then test it by loading up in both server and client applications simultaniously.

## QMBTServer
This is the Qt version of the server program. You can use this to emulate your own device or some device you need to integrate in the system. The GUI monitors any register changed in real-time, and allows changing registers at your convenience. You can also enable debug-level logging to see the lowlevel traffic from your clients.

## QMBTClient
This is the Qt version of the client program. You can use this to interrogate your device, write values to your server, monitor register changes in real-time and/or log values to disk in CSV format. You can also enable debug-level logging to see the lowlevel traffic to your server.

## MBTServer
This is the CLI version of the server program. You can use this to run a server process in the background.

## MBTClient
This is the CLI version of the client program. Not very useful at the moment, but you can use it to download a JSON snapshot of the current server registers, which can be parsed and logged to disk as a simple monitoring service.
