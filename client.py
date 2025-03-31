import machine
import network
import ujson
import mdns
import main
import serverinfo

def WiFiStatusCode(status):
    if status == network.STAT_IDLE:
        return "WL_IDLE\n"
    if status == network.STAT_CONNECTING:
        return "WL_CONNECTING\n"
    if status ==  network.STAT_WRONG_PASSWORD:
        return "WL_WRONG_PASSWORD\n"
    if status ==  network.STAT_NO_AP_FOUND:
        return "WL_NO_AP_FOUND\n"
    if status ==  network.STAT_CONNECT_FAILED:
        return "WL_CONNECT_FAILED\n"
    if status ==  network.STAT_GOT_IP:
        return "WL_GOP_IP\n"

def webSocketEvent(payload):
    string = f"[WSc] get text: {payload}\n"
    main.SERIAL.write(string)
    payload = ujson.dumps(main.doc)
    title = main.doc["title"]
    if title == "GetData":
        MyStatus = {}
        MyStatus["title"] = "GetData"
        if main.modeDebug:
            MyStatus["debug"] = "No"
        else:
            MyStatus["debug"] = "Yes"
        if main.CH1Mode:
            MyStatus["ch1_mode"] = "Wash"
        else:
            MyStatus["ch1_mode"] = "Dry"
        if main.CH2Mode:
            MyStatus["ch2_mode"] = "Wash"
        else:
            MyStatus["ch2_mode"] = "Dry"
        if main.CH1CurrStatus:
            MyStatus["ch1_status"] = "Not Working"
        else:
            MyStatus["ch1_status"] = "Working"
        if main.CH2CurrStatus:
            MyStatus["ch2_status"] = "Not Working"
        else:
            MyStatus["ch2_status"] = "Working"
        MyStatus["CH1_Curr_W"] = main.CH1CurrW
        MyStatus["CH2_Curr_W"] = main.CH2CurrW
        MyStatus["CH1_Flow_W"] = main.CH1FlowW
        MyStatus["CH2_Flow_W"] = main.CH2FlowW
        MyStatus["CH1_Curr_D"] = main.CH1CurrD
        MyStatus["CH2_Curr_D"] = main.CH2CurrD
        MyStatus["CH1_EndDelay_W"] = main.CH1EndDelayW
        MyStatus["CH2_EndDelay_W"] = main.CH2EndDelayW
        MyStatus["CH1_EndDelay_D"] = main.CH1EndDelayD
        MyStatus["CH2_EndDelay_D"] = main.CH2EndDelayD
        MyStatus["ch1_deviceno"] = main.CH1DeviceNo
        MyStatus["ch2_deviceno"] = main.CH2DeviceNo
        MyStatus["ch1_current"] = main.ampsTRMS1
        MyStatus["ch2_current"] = main.ampsTRMS2
        MyStatus["ch1_flow"] = main.CH1LHour
        MyStatus["ch2_flow"] = main.CH2LHour
        MyStatus["ch1_drain"] = main.CH1WaterSensorData
        MyStatus["ch2_drain"] = main.CH2WaterSensorData
        MyStatus["wifi_ssid"] = main.apSsid
        MyStatus["wifi_rssi"] = main.WiFi.status('rssi')
        MyStatus["wifi_ip"] = str(main.WiFi.ifconfig()[0])
        MyStatus["mac"] = main.WiFi.config('mac')
        MyStatus["fw_ver"] = serverinfo.BUILD_DATE
        MyStatus_String = ujson.dumps(MyStatus)
        main.webSocket.send(MyStatus_String)

def WiFiGotIP():
    main.SERIAL.write("WiFi connected ")
    main.SERIAL.write(main.WiFi.ifconfig()[0])
    main.SERIAL.write("\n")
    main.webSocket.disconnect()
    main.serverRetryMillis = main.currMillis
    ip = str(main.WiFi.ifconfig()[0])
    data = f"HWID: {str(main.serialNo)}\r\nCH1: {str(main.CH1DeviceNo)}\r\nCH2: {str(main.CH2DeviceNo)}\r\nROOM: {str(main.RoomNo)}"
    
    main.webSocket.connect(
        host=serverinfo.SERVER_DOMAIN,
        port=serverinfo.SERVER_PORT,
        url=serverinfo.SERVER_URL,
        id=str(main.authId), 
        pw=str(main.authPassword),
        HeaderData=data
        )

    main.webSocket.onEvent(webSocketEvent)

    mdns.start(main.deviceName)
    string = f"Host: http://{main.deviceName}.local/\n"
    main.SERIAL.write(string)
    # ota.setupAsyncServer()

def WiFiStationDisconnected():
    main.WiFi.disconnect()
    main.SERIAL.write("WiFi Lost\n")
    main.wifiFail = 1
    main.WiFi.connect(main.apSsid, main.apPassword)

def NetworkInfo():