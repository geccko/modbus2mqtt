import configparser
import logging

"""
[GENERAL]
device-definition 
log
syslog
modbus-interface

[MQTT]
host 
port
username
password
topic
domoticz-topic 
publish 
clientid
force
output-individual
output-json
output-domoticz

[RTU]
rtu-port
rtu-baud
rtu-parity

[TCP]
tcp-host
tcp-port
"""

class configError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class configHolder():
    pass;


class modbusConfig(object):
    def __init__(self, config_file):

        try:
            config = configparser.RawConfigParser()
            read = config.read(config_file)
            if read == []:
                # print("failed to read configfile %s" % config_file)
                raise configError("failed to read configfile {}".format(config_file))
        except Exception as e:
            raise e

        try:
            # general configuration
            section = "GENERAL"
            self.device_definition = config.get("GENERAL", "device_definition")
            self.loglevel = config.get("GENERAL", "loglevel", fallback="INFO")
            self.syslog = config.get("GENERAL", "syslog", fallback=False)
            self.modbus_interface = config.get("GENERAL", "modbus-interface")
            if self.modbus_interface != "TCP" and self.modbus_interface != "RTU":
                raise configError("Invalid value {} for modbus-interface (should be TCP or RTU)".format(self.modbus_interface))

            # MQTT configuration

            section = "MQTT"
            self.mqtt = configHolder()
            self.mqtt.host = config.get("MQTT", "host", fallback="localhost")
            self.mqtt.port = config.getint("MQTT", "port", fallback="1883")
            self.mqtt.username = config.get("MQTT", "username", fallback=None)
            self.mqtt.password = config.get("MQTT", "password", fallback=None)
            self.mqtt.topic = config.get("MQTT", "topic")
            self.mqtt.domoticz_topic = config.get("MQTT", "domoticz_topic", fallback="domotcz/in")
            self.mqtt.clientid = config.get("MQTT", "clientid", fallback="modbus2mqtt")
            self.mqtt.timed_publish = config.getboolean("MQTT", "timed-publish", fallback="False")
            self.mqtt.publish_individual = config.getboolean("MQTT", "publish-individual", fallback="True")
            self.mqtt.publish_json = config.getboolean("MQTT", "publish-json", fallback=False)
            self.mqtt.publish_domoticz = config.getboolean("MQTT", "publish-domoticz", fallback=False)

            # RTU modbus configuration
            if self.modbus_interface == "RTU":
                section = "RTU"
                self.rtu = configHolder()
                self.rtu.port= config.get("RTU", "port")
                self.rtu.baud = config.getint("RTU", "baud", fallback="9600")
                self.rtu.parity = config.get("RTU", "parity", fallback="none")

            # TCP modbus configuration

            if self.modbus_interface == "TCP": 
                section = "TCP"
                self.tcp = configHolder()
                self.tcp.host = config.get("TCP", "host", fallback="localhost")
                self.tcp.port = config.getint("TCP", "port", fallback="502")
        except Exception as e:
          # logging.error("Error parsing configuration section {}: {}".format(section, e))
          raise configError("Error parsing configuration section {}: {}".format(section, e))

