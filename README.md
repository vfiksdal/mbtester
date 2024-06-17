# MBTester
A suite of client's and server's to test and emulate MODBUS implementations. A MODBUS interface is defined in JSON and can be used to simulate both server and client ends of the communication. Leveraged by the pymodbus library it fully supports any RTU, ASCII and TCP/IP combinations you may need in your project.

# Installation
First install a python3 distribution of your choice, winpython works well for windows users, linux/mac users can use what ships with their OS.
Then you need to install some dependencies:

>python -m pip install pyserial pymodbus

Finally you can run the CLI server:
>python mbserver.py --profile Test_Simple.json

Now you can run the CLI client counterpart, downloading the dataset from the server:
>python mbtclient.py --profile Test_Simple.json

# Writing a MODBUS profile
Before you can use MBTester you need a modbus profile. This is a .json file which defines all the registers your device or integration needs. The simple test files in the repo has a set of holding registers as shown below. Each register has an address, a textual description, data type and value. You can also choose to define word-order, byte-order and read/write access for each register if you want to. Please check the other examples for reference.
![image](https://github.com/vfiksdal/mbtester/assets/51258725/27d9f067-4894-4012-aa87-4152d2e58b6c)

You can now load the profile in a CLI server.
>python mbserver.py --profile Test_Simple.json

Alternatively, you can load it in mbtserver.py for a GUI server where you can monitor writes, change registers on the fly etc.
>python mbtserver.py

![image](https://github.com/vfiksdal/mbtester/assets/51258725/3024a616-a2d7-44b3-a08d-8ff132bc94e2)

With the server running you can start a client. Choose the profile you wrote (Must be in the same folder) and the appropriate settings, and connect to the server. You can now monitor the registers in real-time or double-click one to write a new value.
>python mbtclient.py

![image](https://github.com/vfiksdal/mbtester/assets/51258725/ef93e25a-78c5-40c4-839a-9deb1aca6e60)

# Using MBTester
The actual usage of this application depends upon what you want to accomplish with it. But generally speaking you first want to write a profile to define your interface, you can then run the client to test your device or the server to simulate the device. The GUI programs are typically the most usefull as these let you monitor the communication in real-time and change the contents interactively.

