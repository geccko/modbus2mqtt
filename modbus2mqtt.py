#
# modbus2mqtt - Modbus master with MQTT publishing
#
# Written and (C) 2015 by Oliver Wagner <owagner@tellerulam.com>
# Provided under the terms of the MIT license
#
# Requires:
# - Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/
# - modbus-tk for Modbus communication - https://github.com/ljean/modbus-tk/
#

import argparse
import logging
import logging.handlers
import time
import socket
import paho.mqtt.client as mqtt
import serial
import io
import sys
import csv
import signal

import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
from modbus_tk import modbus_tcp
import json
from  modbusConfig import modbusConfig

version = "0.6a"

parser = argparse.ArgumentParser(description='Bridge between ModBus and MQTT')
parser.add_argument('--config', default = "/etc/modbus2mqtt/modbus2mqtt.cfg",
                    help='path to the configuration file')
args = parser.parse_args()
config = modbusConfig(args.config)


if config.loglevel:
    logging.getLogger().setLevel(config.loglevel)
if config.syslog:
    logging.getLogger().addHandler(logging.handlers.SysLogHandler())
else:
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

changed = False
valuedict = {}

topic = config.mqtt.topic
if not topic.endswith("/"):
    topic += "/"

domoticz_topic = config.mqtt.domoticz_topic

logging.info('Starting modbus2mqtt V%s with topic prefix \"%s\"' %
             (version, topic))


def signal_handler(signal, frame):
    print('Exiting ' + sys.argv[0])
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class Register:

    def __init__(self, topic, frequency, slaveid, functioncode, register, size,
                 format, domoticzIdx, publishIndividual):
        self.topic = topic
        self.domoticzIdx = domoticzIdx
        self.frequency = int(frequency)
        self.slaveid = int(slaveid)
        self.functioncode = int(functioncode)
        self.register = int(register)
        self.size = int(size)
        self.format = format.split(":", 2)
        self.publishIndividual = publishIndividual
        self.next_due = 0
        self.lastval = None
        self.last = None

    def checkpoll(self, updateCallback):
        if self.next_due < time.time():
            self.poll(updateCallback)
            self.next_due = time.time() + self.frequency

    def poll(self, updateCallback):
        try:
            res = master.execute(self.slaveid,
                                 self.functioncode,
                                 self.register,
                                 self.size,
                                 data_format=self.format[0])
            r = res[0]
            if len(self.format) >= 3:
                r = r * float(self.format[2])
            if len(self.format) >= 2:
                r = self.format[1] % r
            if r != self.lastval or (
                    config.mqtt.timed_publish and (time.time() - self.last) > config.mqtt.timed_interval):
                self.lastval = r
                fulltopic = topic + "status/" + self.topic
                if self.publishIndividual:
                    logging.info("Publishing individual " + fulltopic)
                    mqc.publish(fulltopic, self.lastval, qos=0, retain=True)
                if config.mqtt.publish_domoticz and self.domoticzIdx != None:
                    domo_val = {}
                    domo_val["idx"] = int(self.domoticzIdx)
                    domo_val["nvalue"] = 0
                    domo_val["svalue"] = str(self.lastval)
                    domo_json = json.dumps(domo_val)
                    logging.info("Publishing domoticz topic: {}, idx: {}".format(domoticz_topic, self.domoticzIdx))
                    mqc.publish(domoticz_topic, domo_json, qos=0, retain=True)
                self.last = time.time()
                updateCallback(self.topic, self.lastval)
        except modbus_tk.modbus.ModbusError as exc:
            logging.error(
                "Error reading " + self.topic + ": Slave returned %s - %s", exc,
                exc.get_exception_code())
        except Exception as exc:
            logging.error("Error reading " + self.topic + ": %s", exc)


registers = []
defaultrow = {
    "Size": 1,
    "Format": ">H",
    "Frequency": 60,
    "Slave": 1,
    "FunctionCode": 4,
    "DomoticzIdx": None
}

# Now lets read the register definition
if sys.version > '3':
    csvfile = open(config.device_definition, newline = '')
else:
    csvfile = open(config.device_definition, "r") 

with csvfile:
    dialect = csv.Sniffer().sniff(csvfile.read(8192))
    csvfile.seek(0)
    reader = csv.DictReader(csvfile,
                            fieldnames=[
                                "Topic", "Register", "DomoticzIdx", "Size",
                                "Format", "Multiplier", "Frequency", "Slave",
                                "FunctionCode"
                            ],
                            dialect="excel")
    for row in reader:
        # Skip header row
        if row["Frequency"] == "Frequency":
            continue
        # Skip Comment and empty lines (no toic)
        if row["Topic"] == None or row["Topic"] =="":
            continue
        if row["Topic"][0] == "#":
            continue
       
        if row["Topic"] == "DEFAULT":
            temp = dict(
                (k, v) for k, v in row.items() if v is not None and v != "")
            defaultrow.update(temp)
            continue
        freq = row["Frequency"]
        if freq is None or freq == "":
            freq = defaultrow["Frequency"]
        slave = row["Slave"]
        if slave is None or slave == "":
            slave = defaultrow["Slave"]
        fc = row["FunctionCode"]
        if fc is None or fc == "":
            fc = defaultrow["FunctionCode"]
        fmt = row["Format"]
        if fmt is None or fmt == "":
            fmt = defaultrow["Format"]
        size = row["Size"]
        if size is None or size == "":
            size = defaultrow["Size"]
        domoticz_idx = row["DomoticzIdx"]
        if domoticz_idx == None or domoticz_idx == "":
            domoticz_idx = defaultrow["DomoticzIdx"]

        r = Register(row["Topic"], freq, slave, fc, row["Register"], size, fmt,
                     domoticz_idx, config.mqtt.publish_json)
        registers.append(r)

logging.info('Read %u valid register definitions from \"%s\"' %
             (len(registers), config.device_definition))


def messagehandler(mqc, userdata, msg):

    try:
        (prefix, function, slaveid, functioncode,
         register) = msg.topic.split("/")
        if function != 'set':
            return
        if int(slaveid) not in range(0, 255):
            logging.warning("on message - invalid slaveid " + msg.topic)
            return

        if not (int(register) >= 0 and int(register) < sys.maxint):
            logging.warning("on message - invalid register " + msg.topic)
            return

        if functioncode == str(cst.WRITE_SINGLE_COIL):
            logging.info("Writing single coil " + register)
        elif functioncode == str(cst.WRITE_SINGLE_REGISTER):
            logging.info("Writing single register " + register)
        else:
            logging.error("Error attempting to write - invalid function code " +
                          msg.topic)
            return

        res = master.execute(int(slaveid),
                             int(functioncode),
                             int(register),
                             output_value=int(msg.payload))

    except Exception as e:
        logging.error("Error on message " + msg.topic + " :" + str(e))


def connecthandler(mqc, userdata, rc):
    logging.info("Connected to MQTT broker with rc=%d" % (rc))
    mqc.subscribe(topic + "set/+/" + str(cst.WRITE_SINGLE_REGISTER) + "/+")
    mqc.subscribe(topic + "set/+/" + str(cst.WRITE_SINGLE_COIL) + "/+")
    mqc.publish(topic + "connected", 2, qos=1, retain=True)


def disconnecthandler(mqc, userdata, rc):
    logging.warning("Disconnected from MQTT broker with rc=%d" % (rc))


def updateCallback(topic, value):
    global changed
    global valuedict
    changed = True
    valuedict[topic] = value


def jsonOutput(mqc, valueDict):
    valueJson = json.dumps(valueDict)
    fulltopic = topic + "status/"
    logging.info("Publishing " + fulltopic)
    mqc.publish(fulltopic, valueJson, qos=0, retain=True)


try:
    logging.info("Connecting to MQTT server {}:{}".format(config.mqtt.host, config.mqtt.port))
    clientid = config.mqtt.clientid + "-" + str(time.time())
    mqc = mqtt.Client(client_id=clientid)
    if config.mqtt.username:
        mqc.username_pw_set(config.mqtt.username, config.mqtt.password)
    mqc.on_connect = connecthandler
    mqc.on_message = messagehandler
    mqc.on_disconnect = disconnecthandler
    mqc.will_set(topic + "connected", 0, qos=2, retain=True)
    mqc.disconnected = True
    mqc.connect(config.mqtt.host, port = config.mqtt.port, keepalive = 60)
    mqc.loop_start()

    if config.modbus_interface == "RTU":
        master = modbus_rtu.RtuMaster(
            serial.serial_for_url(config.rtu.port,
                                  baudrate=config.rtu.baud,
                                  parity=config.rtu.parity[0].upper()))
    elif config.modbus_interface == "TCP":
        logging.info("opening TCP connection to modbus-TCP  server at {}:{}".format(config.tcp.host, config.tcp.port))
        master = modbus_tcp.TcpMaster(config.tcp.host, config.tcp.port)
    else:
        logging.error(
            "You must specify a valid modbus access method, either RTU or TCP")
        sys.exit(1)
    logging.info("Done")
    master.set_verbose(True)
    master.set_timeout(5.0)

    while True:
        for r in registers:
            r.checkpoll(updateCallback)
        if changed and config.mqtt.publish_json:
            jsonOutput(mqc, valuedict)
            changed = False
        time.sleep(1)

except Exception as e:
    logging.error("Unhandled error [" + str(e) + "]")
    sys.exit(1)
