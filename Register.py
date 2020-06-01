import time
import logging
import modbus_tk
import json

class Register:

    def __init__(self, mqtt_config, topic, frequency, slaveid, functioncode, register, size,
                 format, domoticzIdx):
        self.mqtt_config = mqtt_config
        self.topic = topic
        self.domoticzIdx = domoticzIdx
        self.frequency = int(frequency)
        self.slaveid = int(slaveid)
        self.functioncode = int(functioncode)
        self.register = int(register)
        self.size = int(size)
        self.format = format.split(":", 2)
        
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
                                 data_format=self.format[0])
            r = res[0]
            if len(self.format) >= 3:
                r = r * float(self.format[2])
            if len(self.format) >= 2:
                r = self.format[1] % r
            if r != self.lastval or (
                    self.mqtt_config.timed_publish and (time.time() - self.last) > self .mqtt_config.timed_interval):
                self.lastval = r
                fulltopic = self.mqtt_config.topic_prefix + "status/" + self.topic
                if self.mqtt_config.publish_individual:
                    logging.info("Publishing individual " + fulltopic)
                    mqc.publish(fulltopic, self.lastval, qos=0, retain=True)
                if self.mqtt_config.publish_domoticz and self.domoticzIdx != None:
                    domo_val = {}
                    domo_val["idx"] = int(self.domoticzIdx)
                    domo_val["nvalue"] = 0
                    domo_val["svalue"] = str(self.lastval)
                    domo_json = json.dumps(domo_val)
                    logging.info("Publishing domoticz topic: {}, idx: {}".format(self.mqtt_config.domoticz_topic, self.domoticzIdx))
                    mqc.publish(self.mqtt_config.domoticz_topic, domo_json, qos=0, retain=True)
                self.last = time.time()
                updateCallback(self.topic, self.lastval)
        except modbus_tk.modbus.ModbusError as exc:
            logging.error(
                "Error reading " + self.topic + ": Slave returned %s - %s", exc,
                exc.get_exception_code())
        except Exception as exc:
            logging.error("Error reading " + self.topic + ": %s", exc)


