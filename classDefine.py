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
    def __init__(self):
        self.inPinI = None
        self.ICAL = 0
        self.offsetI = 0
        self.filteredI = 0
        self.sumI = 0
        self.sqI = 0
        self.Irms = 0
        
        self.inPinV = 0
        self.VCAL = 0
        self.PHASECAL = 0
        self.offsetV = 0
    
    def current(self, inPinI, ICAL):
        self.inPinI = inPinI
        self.ICAL = ICAL
        self.offsetI = ADC_COUNTS >> 1
    
    def calcIrms(self, number):
        adc = machine.ADC(self.inPinI)

        adc.width(machine.ADC.WIDTH_12BIT)

        self.sumI = 0

        for n in range(number):
            sampleI = adc.read()

            self.offsetI = (self.offsetI + (sampleI - self.offsetI) / 1024)
            self.filteredI = sampleI - self.offsetI
            
            self.sqI = self.filteredI * self.filteredI
            self.sumI += self.sqI

            time.sleep(0.001)

        I_RATIO = self.ICAL * ((SUPPLY_VOLTAGE / 1000.0) / ADC_COUNTS)
        self.Irms = I_RATIO * math.sqrt(self.sumI / number)

        self.sumI = 0
        
        return self.Irms

class WebSocketClient: