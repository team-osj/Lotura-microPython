import machine
import ujson
import main

def SendStatus(ch, status):
    if ch == 1 and main.CH1Live == False:
        return 1
    if ch == 2 and main.CH2Live == False:
        return 1
    if main.WiFi.isconnected() and main.webSocket.isConnected() == True:
        CurrStatus = {
            "title": "Update"
        }
        if ch == 1:
            CurrStatus["id"] = main.CH1DeviceNo
            CurrStatus["type"] = main.CH1TimeSendFlag
            main.CH1TimeSendFlag = 0
        if ch == 2:
            CurrStatus["id"] = main.CH2DeviceNo 
            CurrStatus["type"] = main.CH2TimeSendFlag
            main.CH2TimeSendFlag = 0
        CurrStatus["state"] = status
        CurrStatusString = ujson.dumps(CurrStatus)
        main.webSocket.send(CurrStatusString) 
        return 0
    else:
        main.SERIAL.write("SendStatus Fail - No Server Connection\n")

def SendLog(ch, log):