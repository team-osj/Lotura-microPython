import machine
import ujson
import math
import time
import base64
from websocket import create_connection
import send
import main

ADC_BITS = 12
ADC_COUNTS = 1 << ADC_BITS

SUPPLY_VOLTAGE = 3.3

#class
class Preferences:
    def __init__(self, filename="config.json"):
        self.filename = filename
        try:
            with open(self.filename, 'r') as file:
                self.data = ujson.load(file)
        except (OSError, ValueError):
            self.data = {}
    
    def begin(self, section, create=False):
        if section not in self.data and create:
            self.data[section] = {}
    
    def putString(self, key, value):
        self.data[key] = str(value)
        self.save()
    
    def putFloat(self, key, value):
        self.data[key] = float(value)
        self.save()
    
    def putUInt(self, key, value):
        self.data[key] = int(value)
        self.save()
    
    def putBool(self, key, value):
        self.data[key] = bool(value)
        self.save()

    def getString(self, key, default=""):
        return self.data.get(key, default)
    
    def getFloat(self, key, default=0.0):
        return float(self.data.get(key, default))
    
    def getUInt(self, key, default=0):
        return int(self.data.get(key, default))
    
    def getBool(self, key, default=False):
        return bool(self.data.get(key, default))
    
    def save(self):
        with open(self.filename, 'w') as file:
            ujson.dump(self.data, file)

class EnergyMonitor:

class WebSocketClient: