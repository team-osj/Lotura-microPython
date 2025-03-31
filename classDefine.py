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
    def __init__(self):
        self.ws = None
        self.isconnected = False

    def _createAuthorizationHeader(self, id, pw):
        if id and pw:
            authString = f"{id}:{pw}"
            authBase64 = base64.b64encode(authString.encode('utf-8')).decode('utf-8')
            return {"Authorization": f"Basic {authBase64}"}
        return {}

    def _parseHeaderData(self, data):
        headers = {}
        lines = data.split("\r\n")
        for line in lines:
            if line.strip():
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        return headers

    def connect(self, host, port, url, id=None, pw=None, HeaderData=None):
        try:
            parsed_headers = self._parseHeaderData(HeaderData)

            headers = {
                **parsed_headers,
                **self._createAuthorizationHeader(id, pw)
            }

            url = f"wss://{host}:{port}{url}"

            self.ws = create_connection(url, sslopt={"certfile": None, "keyfile": None}, headers=headers)
            self.isconnected = True
            string = f"[WSc] Connected to url: {url}\n"
            main.SERIAL.write(string)
            main.lastPingMillis = time.tick_ms()
            main.pingFlag = True
            if main.modeDebug:
                if main.CH1Live == True:
                    send.SendStatus(1, main.CH1CurrStatus)
                if main.CH2Live == True:
                    send.SendStatus(2, main.CH2CurrStatus)
        except Exception as e:
            print(f"Failed to connect: {e}")

    def onEvent(self, event, callback):
        if self.ws:
            try:
                message = self.ws.recv()
                if event in message:
                    callback(message)
                if "ping" in message.lower():
                    self.ws.send("pong")
                    main.lastPingMillis = time.tick_ms()
            except Exception as e:
                string = f"Error while handling event: {e}\n"
                main.SERIAL.write(string)

    def send(self, message):
        if self.ws and self.isconnected:
            try:
                self.ws.send(message)
            except Exception as e:
                string = f"Failed to send message: {e}\n"
                main.SERIAL.write(string)

    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.isconnected = False
            main.SERIAL.write("[WSc] Disconnected!\n")

    def isConnected(self):
        return self.isconnected