import json
import time
import logging

class hass_discovery:
    def __init__(self, sw_version, dev_name, topic_prefix):
        self.sw_version = sw_version
        self.dev_name = dev_name
        self.topic_prefix = topic_prefix
        self.hass_dict = {}

    def addRegister(self, param_name, unit, icon):
        hass_struct = {
            "name": self.dev_name + " " + param_name,
            "stat_t": self.topic_prefix + "SENSOR",
            "avty_t": self.topic_prefix + "connected",
            "pl_avail": "Online",
            "pl_not_avail": "Offline",
            "uniq_id": self.dev_name + "_" + param_name, 
            "dev": {
                "ids": [
                    self. dev_name
                ],
                "name" : self.dev_name,
                "sw" : self.sw_version
            },
            "unit_of_meas": unit,
            "frc_upd": True,
            "val_tpl": "{{value_json." + param_name +"}}"
            }

        if icon:
            hass_struct["ic"] = icon
        else:
                hass_struct["dev_cla"] = "power"
        hass_json = json.dumps(hass_struct, ensure_ascii = False)
        logging.debug("Adding key {} : {}".format(param_name, hass_json))
        self.hass_dict[param_name] = hass_json
        
    def publish(self, mqttc):
        for key in self.hass_dict:
            logging.debug("publishing sensor {}: {}".format(key,json.dumps(self.hass_dict[key]) ))
            mqttc.publish("homeassistant/sensor/" + self.dev_name + '_' + key + "/config", 
                    self.hass_dict[key], retain = True)