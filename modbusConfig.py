import configparser
import logging

class configError(Exception):
    def __init__(self, message):
        self.message = message
        super(configError, self).__init__(self, self.message)

class configHolder():
    pass;

class modbusConfig(object):
    def __init__(self, config_file):

        try:
            config = configparser.RawConfigParser()
            read = config.read(config_file)
            if read == []:
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
            self.mqtt.port = config.getint("MQTT", "port", fallback=1883)
            self.mqtt.username = config.get("MQTT", "username", fallback=None)
            self.mqtt.password = config.get("MQTT", "password", fallback=None)
            self.mqtt.topic = config.get("MQTT", "topic")
            self.mqtt.domoticz_topic = config.get("MQTT", "domoticz_topic", fallback="domotcz/in")
            self.mqtt.clientid = config.get("MQTT", "clientid", fallback="modbus2mqtt")
            self.mqtt.timed_publish = config.getboolean("MQTT", "timed-publish", fallback=False)
            self.mqtt.timed_interval = config.getint("MQTT", "timed-interval", fallback=15)
            self.mqtt.publish_individual = config.getboolean("MQTT", "publish-individual", fallback="True")
            self.mqtt.publish_json = config.getboolean("MQTT", "publish-json", fallback=True)
            self.mqtt.publish_domoticz = config.getboolean("MQTT", "publish-domoticz", fallback=True)

            # RTU modbus configuration
            if self.modbus_interface == "RTU":
                section = "RTU"
                self.rtu = configHolder()
                self.rtu.port= config.get("RTU", "port")
                self.rtu.baud = config.getint("RTU", "baud", fallback=9600)
                self.rtu.parity = config.get("RTU", "parity", fallback="None")

            # TCP modbus configuration

            if self.modbus_interface == "TCP": 
                section = "TCP"
                self.tcp = configHolder()
                self.tcp.host = config.get("TCP", "host", fallback="localhost")
                self.tcp.port = config.getint("TCP", "port", fallback=502)
        except Exception as e:
          raise configError("Error parsing configuration section {}: {}".format(section, e))

