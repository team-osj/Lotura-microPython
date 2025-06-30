import uasyncio as asyncio
import usocket as socket
import network
import ujson
import utime
import machine
import math
import sys
import ubinascii
import uos
from machine import Pin, ADC
import webrepl
import ntptime

# Server configuration (from ServerInfo.h)
serverDomain = "lotura-prod.xquare.app"
serverPort = 443
serverUrl = "/device"
authType = "Basic"
ntpServer = "kr.pool.ntp.org"
timeZone = 9
buildDate = "Jun 10 2025 12:27:00"

# GPIO Definitions
pinStatus = 17
pinCh1Led = 18
pinCh2Led = 19
pinCh1Mode = 33
pinCh2Mode = 32
pinDebug = 14
pinCt1 = 35
pinCt2 = 34
pinFlow1 = 27
pinFlow2 = 26
pinDrain1 = 23
pinDrain2 = 25

pingLateMillis = 21500
sensPeriod = 500

# Global variables
isRebooting = False
isPingFlag = False
previousMillis = utime.ticks_ms()
previousMillisEnd1 = 0
previousMillisEnd2 = 0
ledMillisPrev = 0
currMillis = 0
serverRetryMillis = 0
lastPingMillis = 0

m1 = 0
m2 = 0
timeSendFlag1 = 0
timeSendFlag2 = 0
isModeDebug = False
ledStatus = 0

# Operating conditions
ch1CurrW = 0.2
ch2CurrW = 0.2
ch1FlowW = 50
ch2FlowW = 50
ch1CurrD = 0.5
ch2CurrD = 0.5
ch1EndDelayW = 10 * 10000
ch2EndDelayW = 10 * 10000
ch1EndDelayD = 10 * 1000
ch2EndDelayD = 10 * 1000

isCh1Mode = False
isCh2Mode = False
ch1CurrStatus = 1
ch2CurrStatus = 1
ch1Cnt = 1
ch2Cnt = 1
isCh1Live = True
isCh2Live = True

defaultDeviceName = "OSJ_"
deviceName = ""
apSsid = ""
apPasswd = ""
serialNo = "0"
authId = ""
authPasswd = ""
ch1DeviceNo = "1"
ch2DeviceNo = "2"
roomNo = "0"
isWifiFail = 1

# Current measurement
ampsTrms1 = 0.0
ampsTrms2 = 0.0

# Water sensor
waterSensorData1 = 0
waterSensorData2 = 0

# Flow sensor
flowFrequency1 = 0
flowFrequency2 = 0
lHour1 = 0
lHour2 = 0

# JSON logs
jsonLogFlag1 = 0
jsonLogFlag2 = 0
jsonLogFlag1C = 0
jsonLogFlag2C = 0
jsonLogFlag1F = 0
jsonLogFlag2F = 0
jsonLogFlag1W = 0
jsonLogFlag2W = 0
jsonLogMillis1 = 0
jsonLogMillis2 = 0
jsonLogCnt1 = 1
jsonLogCnt2 = 1
jsonLog1 = {}
jsonLog2 = {}

# Pin setup
statusPin = Pin(pinStatus, Pin.OUT)
ch1Led = Pin(pinCh1Led, Pin.OUT)
ch2Led = Pin(pinCh2Led, Pin.OUT)
ch1Mode = Pin(pinCh1Mode, Pin.IN, Pin.PULL_UP)
ch2Mode = Pin(pinCh2Mode, Pin.IN, Pin.PULL_UP)
debugPin = Pin(pinDebug, Pin.IN)
ct1 = ADC(Pin(pinCt1))
ct2 = ADC(Pin(pinCt2))
flow1 = Pin(pinFlow1, Pin.IN)
flow2 = Pin(pinFlow2, Pin.IN)
drain1 = Pin(pinDrain1, Pin.IN)
drain2 = Pin(pinDrain2, Pin.IN)

# ADC configuration
ct1.atten(ADC.ATTN_11DB)
ct2.atten(ADC.ATTN_11DB)

# WiFi setup
staIf = network.WLAN(network.STA_IF)
staIf.active(True)