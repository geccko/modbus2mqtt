modbus2mqtt
===========

  Written and (C) 2015 Oliver Wagner <owagner@tellerulam.com> 
  Extended (C) 2020 Louis Lagendijk <louis.lagendijk@gmail.com>
  
  Provided under the terms of the MIT license.

Install:
<your python executable> setup.py install, e.g.
python3 setup.py install

Overview
--------
modbus2mqtt is a Modbus master which continously polls slaves and publishes
register values via MQTT.

It is intended as a building block in heterogenous smart home environments where 
an MQTT message broker is used as the centralized message bus.
See https://github.com/mqtt-smarthome for a rationale and architectural overview.

Modbus2mqtt can publish results from a modbus devices in 3 formats:
* *Individual registers to the <topic_prefix>/status/<registername>
* *As single json message for the defined registers to <topic_prefix>/status
* *To /domoticz/in with the index set to the value defined in the register file


Dependencies
------------
* Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/
* modbus-tk for Modbus communication - https://github.com/ljean/modbus-tk/


Command line options
--------------------
    usage: modbus2mqtt [-h] [--config CONFIG]

    Bridge between ModBus and MQTT

    optional arguments:
      -h, --help       show this help message and exit
      --config CONFIG  path to the configuration file

Configuration file
------------------
The example configuration file contains details on the options that can be set. 
      
Register definition
-------------------
The Modbus registers which are to be polled are defined in a CSV file with
the following columns:

* *Topic suffix*
  The topic where the respective individual register will be published into. Will
  be prefixed with the global topic prefix and "status/".
* *Register offset*
  The register number, depending on the function code. Zero-based.
* *DomoticzIdx*, the index for the register used in Domoticz for the device
* *Size* (in words)*
  The register size in (16 bits) words.
* *DataFormat*, uses the Python
  "struct" module notation. Common examples:
    - >H unsigned short (1 16 bit word)
    - >h signed short (1 16 bit word)
     - >I Integer (dword / 2 words)
     - >i unsigned integer (dword / 2 words)
    - >f float
* *Multiplier*, result is scaled by multiplying the register by the multiplier  
* *OutputFormat*, is optional and specifies a Python format string, e.g.
      %.2f to format the value to two decimal digits.
* *Frequency*, How often the register is to be polled, in seconds. Only integers.
* *Slave* The Modbus address of the slave to query. Defaults to 1.
* *FunctionCode* The Modbus function code to use for querying the register. Defaults
  to 3 READ HOLDING REGISTER). Only change if you know what you are doing.

Not all columns need to be specified. Unspecified columns take their
default values. The default values for subsequent rows can be set
by specifying a magic topic suffix of *DEFAULT*

Topics
------
Individual Values are published as simple strings to topics with the general <prefix>,
the function code "/status/" and the topic suffix specified per register.
A value will only be published if it's textual representation has changed,
e.g. _after_ formatting has been applied. The published MQTT messages have
the retain flag set.

Json values are published as soon as any register has changed its textual represntation.
Values are published as a json string containing all register topics and their values.
Published.

Domoticz messages are pubished to the topic "domoticz/in" with the index (idx) value 
specified in hte register file. the topic can be changed by setting the desired value in
the coniguration file.

A special topic "<prefix>/connected" is maintained. 
It's a enum stating whether the module is currently running and connected to 
the broker (1) and to the Modbus interface (2).

Setting Modbus coils (FC=5) and registers (FC=6)
------------------------------------------------

modbus2mqtt subscibes to two topics:

- prefix/set/+/5/+  # where the first + is the slaveId and the second is the register
- prefix/set/+/6/+  # payload values are written the the devices (assumes 16bit Int)

There is only limited sanity checking currently on the payload values.


Changelog
---------
* 0.6 - 2020-06-01 - Louis Lagendijk
  - Replaced command line options by a configuration file
  - Added json messages
  - Added support for domoticz output

* 0.4 - 2015/07/31 - nzfarmer
  - added support for MQTT subscribe + Mobdus write
    Topics are of the form: prefix/set/<slaveid (0:255)>/<fc (5,6)>/<register>  (payload = value to write)
  - added CNTL-C for controlled exit
  - added --clientid for MQTT connections
  - added --force to repost register values regardless of change every x seconds where x >0
	
* 0.3 - 2015/05/26 - owagner
  - support optional string format specification
* 0.2 - 2015/05/26 - owagner
  - added "--rtu-parity" option to set the parity for RTU serial communication. Defaults to "even",
    to be inline with Modbus specification
  - changed default for "--rtu-baud" to 19200, to be inline with Modbus specification

* 0.1 - 2015/05/25 - owagner
  - Initial version
  
