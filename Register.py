#
# Written and (C) 2015 by Oliver Wagner <owagner@tellerulam.com>
# Provided under the terms of the MIT license
# Extended and refactored (C) 2020 by Louis Lagendijk >louis.lagendijk@gmail.com>
#
import time
import logging
import modbus_tk
import json

class Register:

    def __init__(self, mqtt_config, topic, register, domoticzIdx, size, data_format, multiplier, output_format, frequency, slaveid, functioncode):
        self.mqtt_config = mqtt_config
        self.topic = topic
        self.register = int(register)
        if mqtt_config.publish_domoticz and domoticzIdx != None and domoticzIdx != "":
            self.publish_domoticz = True
            self.domoticzIdx = int(domoticzIdx)
        else:
            self.publish_domoticz = False
        self.size = int(size)
        self.data_format = data_format
        self.multiplier = float(multiplier)
        self.output_format = output_format
        self.frequency = int(frequency)
        self.slaveid = int(slaveid)
        self.functioncode = int(functioncode)
        
        self.next_due = 0
        self.lastval = None
        self.last = None

    def checkpoll(self, master, mqc,updateCallback):
        if self.next_due < time.time():
            self.poll(master, mqc, updateCallback)
            self.next_due = time.time() + self.frequency

    def poll(self, master, mqc, updateCallback):
        try:
            res = master.execute(self.slaveid,
                                 self.functioncode,
                                 self.register,
                                 self.size,
                                 data_format=self.data_format)
            r = res[0] * self.multiplier
            r = self.output_format % r
            if r != self.lastval or (
                    self.mqtt_config.timed_publish and (time.time() - self.last) > self .mqtt_config.timed_interval):
                self.lastval = r
                fulltopic = self.mqtt_config.topic_prefix + "status/" + self.topic
                if self.mqtt_config.publish_individual:
                    logging.debug("Publishing individual " + fulltopic)
                    mqc.publish(fulltopic, self.lastval, qos=0, retain=True)
                if self.publish_domoticz:
                    domo_val = {}
                    domo_val["idx"] = int(self.domoticzIdx)
                    domo_val["nvalue"] = 0
                    domo_val["svalue"] = str(self.lastval)
                    domo_json = json.dumps(domo_val)
                    logging.debug("Publishing domoticz topic: {}, idx: {}".format(self.mqtt_config.domoticz_topic, self.domoticzIdx))
                    mqc.publish(self.mqtt_config.domoticz_topic, domo_json, qos=0, retain=True)
                self.last = time.time()
                updateCallback(self.topic, self.lastval)
        except modbus_tk.modbus.ModbusError as exc:
            logging.error(
                "Error reading " + self.topic + ": Slave returned %s - %s", exc,
                exc.get_exception_code())
        except Exception as exc:
            logging.error("Error reading " + self.topic + ": %s", exc)


