#
# Written and (C) 2020 by Louis Lagendijk >louis.lagendijk@gmail.com>
# Provided under the terms of the MIT license
#
import configparser
import logging


class configError(Exception):

    def __init__(self, message):
        self.message = message
        super(configError, self).__init__(self, self.message)


class configHolder():
    pass


class modbusConfig(object):

    def __init__(self, config_file):

        try:
            config = configparser.RawConfigParser(interpolation = configparser.ExtendedInterpolation())
            read = config.read(config_file)
            if read == []:
                raise configError(
                    "failed to read configfile {}".format(config_file))
        except Exception as e:
            raise e

        try:
            # general configuration
            section = "GENERAL"
            self.device_definition = config.get("GENERAL", "device_definition")
            if self.device_definition == None:
                raise configError('device-definition must be defined')
            self.loglevel = config.get("GENERAL", "loglevel", fallback="INFO")
            self.syslog = config.get("GENERAL", "syslog", fallback=False)
            self.modbus_interface = config.get("GENERAL", "modbus-interface")
            if self.modbus_interface != "TCP" and self.modbus_interface != "RTU":
                raise configError(
                    "Invalid value {} for modbus-interface (should be TCP or RTU)"
                    .format(self.modbus_interface))
            self.devicename = config.get("GENERAL", "devicename")
            if  not self.devicename:
                raise configError("devicename is not specified in section GENERAL")

            # MQTT configuration

            section = "MQTT"
            self.mqtt = configHolder()
            self.mqtt.publish_individual = config.getboolean("MQTT", 
                                                        "publish-individual", 
                                                        fallback=False)
            self.mqtt.publish_json = config.getboolean("MQTT",
                                                       "publish-json",
                                                       fallback=False)
            self.mqtt.publish_domoticz = config.getboolean("MQTT",
                                                           "publish-domoticz",
                                                           fallback=False)
            self.mqtt.publish_homeassistant = config.getboolean("MQTT",
                                                           "publish-homeassistant",
                                                           fallback=False)

            self.mqtt.host = config.get("MQTT", "host", fallback="localhost")
            self.mqtt.port = config.getint("MQTT", "port", fallback=1883)
            self.mqtt.username = config.get("MQTT", "username", fallback=None)
            self.mqtt.password = config.get("MQTT", "password", fallback=None)

            # TODO: rename topic prefix and split into topic and name?
            self.mqtt.topic_prefix = config.get("MQTT", "topic-prefix")
            if self.mqtt.topic_prefix == None:
                raise configError(
                    'mqtt-topic is not defined in MQTT section')
            if not self.mqtt.topic_prefix.endswith("/"):
                self.mqtt.topic_prefix += "/"

            if self.mqtt.publish_domoticz:
                self.mqtt.domoticz_topic = config.get("MQTT",
                                                      "domoticz-topic",
                                                      fallback="domoticz/in")
                if self.mqtt.domoticz_topic == None:
                    raise configError(
                        'domoticz-prefix is not defined in MQTT section')
                if self.mqtt.domoticz_topic.endswith("/"):
                    raise configError('domoticz prefix must not end with a "/"')

            self.mqtt.clientid = config.get("MQTT",
                                            "clientid",
                                            fallback="modbus2mqtt")
            self.mqtt.timed_publish = config.getboolean("MQTT",
                                                        "timed-publish",
                                                        fallback=False)
            self.mqtt.timed_interval = config.getint("MQTT",
                                                     "timed-interval",
                                                     fallback=15)

            # RTU modbus configuration
            if self.modbus_interface == "RTU":
                section = "RTU"
                self.rtu = configHolder()
                self.rtu.port = config.get("RTU", "port")
                if self.rtu.port == None:
                    raise configError('port must be defined in RTU section')
                self.rtu.baud = config.getint("RTU", "baud", fallback=9600)
                self.rtu.parity = config.get("RTU", "parity", fallback="None")

            # TCP modbus configuration

            if self.modbus_interface == "TCP":
                section = "TCP"
                self.tcp = configHolder()
                self.tcp.host = config.get("TCP", "host", fallback="localhost")
                self.tcp.port = config.getint("TCP", "port", fallback=502)
        except Exception as e:
            raise configError(
                "Error parsing configuration section {}: {}".format(section, e))
