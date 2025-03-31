import machine
import main

def putString(key, value):
    string = f"{key} = {value}"
    main.SERIAL.write(string)
    main.preferences.putString(key, value)

def SetDefaultVal():
    main.apSsid = main.preferences.getString("ap_ssid", "")
    main.apPassword = main.preferences.getString("ap_passwd", "")
    main.serialNo = main.preferences.getString("serial_no", "0")
    main.authId = main.preferences.getString("AUTH_ID", "")
    main.authPassword = main.preferences.getString("AUTH_PASSWD", "")

    main.CH1DeviceNo = main.preferences.getString("CH1_DeviceNo", "1")
    main.CH2DeviceNo = main.preferences.getString("CH2_DeviceNo", "2")

    main.CH1CurrW = main.preferences.getFloat("CH1_Curr_W", 0.2)
    main.CH2CurrW = main.preferences.getFloat("CH2_Curr_W", 0.2)
    main.CH1FlowW = main.preferences.getUInt("CH1_Flow_W", 50)
    main.CH2FlowW = main.preferences.getUInt("CH2_Flow_W", 50)
    main.CH1CurrD = main.preferences.getFloat("CH1_Curr_D", 0.5)
    main.CH2CurrD = main.preferences.getFloat("CH2_Curr_D", 0.5)

    main.CH1EndDelayW = main.preferences.getUInt("CH1_EndDelay_W", 10)
    main.CH2EndDelayW = main.preferences.getUInt("CH2_EndDelay_W", 10)
    main.CH1EndDelayD = main.preferences.getUInt("CH1_EndDelay_D", 10)
    main.CH2EndDelayD = main.preferences.getUInt("CH2_EndDelay_D", 10)

    main.CH1Live = main.preferences.getBool("CH1_Live", True)
    main.CH2Live = main.preferences.getBool("CH2_Live", True)

    main.RoomNo = main.preferences.getString("RoomNo", "0")

    main.deviceName = main.defaultDeviceName+main.serialNo

    main.WiFi.config(hostname=str(main.deviceName))
    
    string = f"My Name is : {main.deviceName}\nCH1 : {main.CH1DeviceNo} CH2 : {main.CH2DeviceNo}\n"
    main.SERIAL.write(string)

    if main.authId == "" or main.authPassword == "":
        main.SERIAL.wrtie("NO AUTH CODE!!! YOU NEED TO CONFIG SERVER AUTHENTICATION BY AT+SET_AUTH_ID AND AT+SET_AUTH_PASSWD IN DEBUG MODE!!!")
    if main.apSsid == "":
        main.SERIAL.wrtie("NO WIFI SSID!!! YOU NEED TO CONFIG WIFI BY AT+SETAP_SSID AND AT+SETAP_PASSWD IN DEBUG MODE!!!")
    
    main.CH1EndDelayW *= 10000
    main.CH2EndDelayW *= 10000
    main.CH1EndDelayD *= 1000
    main.CH2EndDelayD *= 1000

    string = f"CH1_Curr_Wash : {main.CH1CurrW} CH2_Curr_Wash : {main.CH2CurrW}\n"
    main.SERIAL.write(string)
    string = f"CH1_Flow_Wash : {main.CH1FlowW} CH1_Flow_Wash : {main.CH2FlowW}\n"
    main.SERIAL.write(string)
    string = f"CH1_Delay_Wash : {main.CH1EndDelayW} CH2_Delay_Wash : {main.CH2EndDelayW}\n"
    main.SERIAL.write(string)
    string = f"CH1_Curr_Dry : {main.CH1CurrD} CH2_Curr_Dry : {main.CH2CurrD}\n"
    main.SERIAL.write(string)
    string = f"CH1_Delay_Dry : {main.CH1EndDelayD} CH1_Delay_Dry : {main.CH2EndDelayD}\n"
    main.SERIAL.write(string)
    string = f"CH1_Enable : {main.CH1Live} CH2_Enable : {main.CH2Live}\n"
    main.SERIAL.write(string)
    