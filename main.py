import machine
import network
import gc
import time
import interrupt
import serverinfo
import value
import loop
import client
import classDefine

#define
PIN_CT1 = 35
PIN_CT2 = 34

PIN_STATUS = machine.Pin(17, machine.Pin.OUT)
PIN_CH1_LED = machine.Pin(18, machine.Pin.OUT)
PIN_CH2_LED = machine.Pin(19, machine.Pin.OUT)
PIN_CH1_MODE = machine.Pin(33, machine.Pin.IN, machine.Pin.PULL_UP)
PIN_CH2_MODE = machine.Pin(32, machine.Pin.IN, machine.Pin.PULL_UP)
PIN_DEBUG = machine.Pin(14, machine.Pin.IN)
PIN_FLOW1 = machine.Pin(27, machine.Pin.IN)
PIN_FLOW2 = machine.Pin(26, machine.Pin.IN)
PIN_DRAIN1 = machine.Pin(23, machine.Pin.IN)
PIN_DRAIN1 = machine.Pin(25, machine.Pin.IN)

PING_LATE_MILLIS = 21500
SENS_PERIOD = 500

#variable
rebooting = False
pingFlag = False

prevMillis = 0
CH1PrevMillisEnd = 0
CH2PrevMillisEnd = 0
ledPrevMillis = 0
currMillis = 0
serverRetryMillis = 0
lastPingMillis = 0

CH1M = 0
CH2M = 0

CH1TimeSendFlag = 0
CH2TimeSendFlag = 0
modeDebug = False
ledStatus = 0

CH1CurrW = 0
CH2CurrW = 0
CH1FlowW = 0
CH2FlowW = 0
CH1CurrD = 0
CH2CurrD = 0

CH1EndDelayW = 0
CH2EndDelayW = 0
CH1EndDelayD = 0
CH2EndDelayD = 0

CH1Mode = False
CH2Mode = False
CH1CurrStatus = 1
CH2CurrStatus = 1
CH1Cnt = 1
CH2Cnt = 1
CH1Live = True
CH2Live = True

defaultDeviceName = "OSJ_"
deviceName = ""
apSsid = ""
apPassword = ""
serialNo = ""
authId = ""
authPassword = ""
CH1DeviceNo = ""
CH2DeviceNo = ""
RoomNo = "0"

wifiFail = 1

ampsTRMS1 = 0
ampsTRMS2 = 0

CH1WaterSensorData = 0
CH2WaterSensorData = 0

CH1FlowFrequency = 0
CH2FlowFrequency = 0
CH1LHour = 0
CH2LHour = 0

CH1JsonLogFlag = 0
CH2JsonLogFlag = 0
CH1JsonLogFlagC = 0
CH2JsonLogFlagC = 0
CH1JsonLogFlagF = 0
CH2JsonLogFlagF = 0
CH1JsonLogFlagW = 0
CH2JsonLogFlagW = 0
CH1JsonLogMillis = 0
CH2JsonLogMillis = 0
CH1JsonLogCnt = 0
CH2JsonLogCnt = 0

CH1JsonLog = {}
CH2JsonLog = {}

CH1SePrevMillis = 0
CH2SePrevMillis = 0
CH1SeCnt = 0
CH2SeCnt = 0

wifiConnected = False

SERIAL = machine.UART(0, baudrate=115200, tx=1, rx=3)
preferences = classDefine.Preferences()

ct1 = classDefine.EnergyMonitor()
ct2 = classDefine.EnergyMonitor()

PIN_FLOW1.irq(trigger=machine.Pin.IRQ_FALLING, handler=interrupt.Flow1)
PIN_FLOW2.irq(trigger=machine.Pin.IRQ_FALLING, handler=interrupt.Flow2)

doc = {}
WiFi = 0

webSocket = classDefine.WebSocketClient()

# AsyncWebServer server(80) 

timer = machine.Timer(0)

#def
def checkWifiStatus(timer):
    global wifiConnected
    if WiFi.isconnected():
        if not wifiConnected:
            wifiConnected = True
            client.WiFiGotIP()
    else:
        if wifiConnected:
            wifiConnected = False
            client.WiFiStationDisconnected()

#main
if __name__ == "__main__":
    WiFi = network.WLAN(network.STA_IF)
    preferences.begin("config", True)
    string = f"FW_VER : {serverinfo.BUILD_DATE}\n"
    SERIAL.write(string)

    ct1.current(PIN_CT1, 30.7)
    ct2.current(PIN_CT2, 30.7)

    value.SetDefaultVal()

    modeDebug = PIN_DEBUG.value()

    CH1Mode = PIN_CH1_MODE.value()
    CH2Mode = PIN_CH2_MODE.value()

    if modeDebug == 0:
        SERIAL.write("YOU ARE IN THE DEBUG MODE !!!\n")
    
    string = f"CH1_Mode : {CH1Mode}\nCH2_Mode : {CH2Mode}\n"
    SERIAL.write(string)

    WiFi.disconnect()

    for i in range(0, 30):
        ct1.calclrms(1480)
        ct2.calclrms(1480)
    
    string = f"Boot Heap : {gc.mem_free()}\n"
    SERIAL.write(string)

    PIN_STATUS.value(1)
    
    timer.init(period=1000, mode=machine.Timer.PERIODIC, callback=checkWifiStatus)

    if apSsid == "":
        SERIAL.write("Skip WiFi Setting Due to No SSID\n")
    else:
        string = f"Connecting to WiFi .. {apSsid}\n"
        SERIAL.write(string)

        if apPassword == "":
            WiFi.connect(apSsid) 
        else:
            WiFi.connect(apSsid, apPassword)

        wifiTimeOut = 0

        while WiFi.isconnected():
            SERIAL.write(".")
            PIN_STATUS.value(0)
            time.sleep(0.1)
            PIN_STATUS.value(1)
            time.sleep(0.1)
            wifiTimeOut += 1

            if wifiTimeOut > 25:
                SERIAL.write("Skip WiFi Connection Due to Timeout")
                break
    
    loop.loop()