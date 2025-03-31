import machine
import esp
import gc
import time
import uasyncio as asyncio
from microdot import Microdot, Response
import main
import serverinfo
import value
import html

def processor(var):
    if var == "DEVICE_NAME":
        return main.deviceName
    if var == "SSID":
        return main.apSsid
    if var == "PASS":
        return main.apPassword
    if var == "RSSI":
        return str(main.WiFi.status('rssi'))
    if var == "WIFI_QUALITY":
        if main.WiFi.isconnected():
            return "WiFi Not Connected"
        rssi = main.WiFI.status('rssi')
        if rssi > -40:
            return "Very Good"
        elif rssi > -60:
            return "Good"
        elif rssi > -70:
            return "Weak"
        else:
            return "Poor"
    if var == "IP":
        return str(main.WiFi.ifconfig()[0])
    if var == "MAC":
        return main.WiFi.config('mac')
    if var == "RoomNo":
        return main.RoomNo
    if var == "TCP_STATUS":
        if main.webSocket.isConnected():
            return "Connected"
        else:
            return "Disconnected"
    if var == "FlashSize":
        return str(esp.flash_size()/1024)
    if var == "Heap":
        return str(gc.mem_free()/1024)
    if var == "BUILD_VER":
        return serverinfo.BUILD_DATE
    if var == "CH1_DeviceNo":
        return main.CH1DeviceNo
    if var == "CH1_Live":
        if(main.CH1Live):
            return "Yes"
        else:
            return "NO"
    if var == "CH1_Mode":
        if(main.CH1Mode):
            return "Wash"
        else:
            return "Dry"
    if var == "CH1_Curr_W":
        return str(main.CH1CurrW)
    if var == "CH1_Flow_W":
        return str(main.CH1FlowW)
    if var == "CH1_Curr_D":
        return str(main.CH1CurrD)
    if var == "CH1_EndDelay_W":
        return str(main.CH1EndDelayW)
    if var == "CH1_EndDelay_D":
        return str(main.CH1EndDelayD)
    if var == "Amps_TRMS1":
        return str(main.ampsTRMS1)
    if var == "WaterSensorData1":
        return str(main.CH1WaterSensorData)
    if var == "l_hour1":
        return str(main.CH1LHour)
    if var == "CH2_DeviceNo":
        return main.CH2DeviceNo
    if var == "CH2_Live":
        if main.CH2Live:
            return "Yes"
        else:
            return "NO"
    if var == "CH2_Mode":
        if main.CH2Mode:
            return "Wash"
        else:
            return "Dry"
    if var == "CH2_Curr_W":
        return str(main.CH2CurrW)
    if var == "CH2_Flow_W":
        return str(main.CH2FlowW)
    if var == "CH2_Curr_D":
        return str(main.CH2CurrD)
    if var == "CH2_EndDelay_W":
        return str(main.CH2EndDelayW)
    if var == "CH2_EndDelay_D":
        return str(main.CH2EndDelayD)
    if var == "Amps_TRMS2":
        return str(main.ampsTRMS2)
    if var == "WaterSensorData2": 
        return str(main.CH2WaterSensorData)
    if var == "l_hour2":
        return str(main.CH2LHour)
    return str()

def convertFileSize(bytes):
    if bytes < 1024:
        return f"{str(bytes)} B"
    elif bytes < 1048576:
        return f"{str(bytes/1024.0)} kB" 
    elif bytes < 1073741824:
        return f"{str(bytes/1048576.0)} MB"  
    
class WebServer: