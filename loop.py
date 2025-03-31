import machine
import nvs
import gc
import time
import main
import judgment 
import setvar
import client
import value

def loop():
    while True:
        main.currMillis = time.ticks_ms()

        if main.pingFlag == True and main.webSocket.isConnected() == True and main.currMillis - main.lastPingMillis >= main.PING_LATE_MILLIS:
            main.pingFlag = False
            main.webSocket.disconnect()
        if main.rebooting:
            time.sleep(0.1)
            machine.reset()
        if main.WiFi.isconnected():
            main.PIN_STATUS.value(1)
            main.wifiFail = 0
        else:
            main.wifiFail = 1
            if main.currMillis - main.ledPrevMillis >= 100:
                main.ledPrevMillis = main.currMillis
                main.PIN_STATUS.value(not (main.PIN_STATUS.value()))
        if main.modeDebug:
            main.ampsTRMS1 = main.ct1.calcIrms(1480)
            main.ampsTRMS2 = main.ct2.calcIrms(1480)

            if main.prevMillis > time.ticks_ms():
                main.prevMillis = time.ticks_ms()
            
            if time.ticks_ms() - main.prevMillis >= main.SENS_PERIOD:
                main.prevMillis = time.ticks_ms()

                main.CH1WaterSensorData = main.PIN_DRAIN1.value()
                main.CH2WaterSensorData = main.PIN_DRAIN2.value()

                main.CH1LHour = (main.CH1FlowFrequency * 60 / 7.5)
                main.CH2LHour = (main.CH2FlowFrequency * 60 / 7.5)

                main.CH1FlowFrequency = 0
                main.CH2FlowFrequency = 0

            if main.CH1Mode:
                judgment.StatusJudgment(main.ampsTRMS1, main.CH1WaterSensorData, main.CH1LHour, main.CH1Cnt, main.CH1M, main.CH1PrevMillisEnd, 1)
            else:
                judgment.DryerStatusJudgment(main.ampsTRMS1, main.CH1Cnt, main.CH1M, main.CH1PrevMillisEnd, 1)
            
            if main.CH2Mode:
                judgment.StatusJudgment(main.ampsTRMS2, main.CH2WaterSensorData, main.CH2LHour, main.CH2Cnt, main.CH2M, main.CH2PrevMillisEnd, 2)
            else:
                judgment.DryerStatusJudgment(main.ampsTRMS2, main.CH2Cnt, main.CH2M, main.CH1PrevMillisEnd, 2)
        else:
            main.currMillis = time.ticks_ms()

            if main.currMillis - main.ledPrevMillis >= 100:
                main.ledPrevMillis = main.currMillis

                if main.ledStatus == 1:
                    main.ledStatus = 0
                    main.PIN_CH1_LED.value(1)
                    main.PIN_CH2_LED.value(0)
                elif main.ledStatus == 0:
                    main.ledStatus = 1
                    main.PIN_CH1_LED.value(0)
                    main.PIN_CH2_LED.value(1)
            if main.SERIAL.any():
                dexc = 0
                SerialData = main.SERIAL.readline()
                dex = int(SerialData.find('+'))
                dex1 = int(SerialData.find('"'))
                end = int(len(SerialData))
                AT_Command = str(SerialData[dex+1, dex1])
                if AT_Command == "HELP":
                    main.SERIAL.write("AT+OK HELP\n")
                elif AT_Command == "SENSDATA_START":
                    main.SERIAL.write("AT+OK SENSDATA_START\n")
                elif AT_Command == "UPDATE":
                    main.SERIAL.write("AT+OK UPDATE\n")
                elif AT_Command == "CH1_SETVAR":
                    main.SERIAL.write("AT+OK CH1_SETVAR\n")
                    setvar.CH1SETVAR(SerialData, dex1, dexc, end)
                elif AT_Command == "CH2_SETVAR":
                    main.SERIAL.write("AT+OK CH2_SETVAR\n")
                    setvar.CH2SETVAR(SerialData, dex1, dexc, end)
                elif AT_Command == "UPDATE":
                    main.SERIAL.write("AT+OK UPDATE\n")
                elif AT_Command == "NETWORK_INFO":
                    main.SERIAL.write("AT+OK NETWORK_INFO\n")
                    client.NetworkInfo()
                elif AT_Command == "SETAP_SSID":
                    main.SERIAL.write("AT+OK SETAP_SSID\n")
                    value.putString("ap_ssid", SerialData[dex1+1, end - 1])
                elif AT_Command == "SETAP_PASSWD":
                    main.SERIAL.write("AT+OK SETAP_PASSWD\n")
                    value.putString("ap_passwd", SerialData[dex1+1, end - 1])
                elif AT_Command == "SET_SERIALNO":
                    main.SERIAL.write("AT+OK SET_SERIALNO\n")
                    value.putString("serial_no", SerialData[dex1+1, end - 1])
                elif AT_Command == "SET_AUTH_ID":
                    main.SERIAL.write("AT+OK SET_AUTH_ID\n")
                    value.putString("AUTH_ID", SerialData.substring(dex1+1, end - 1))
                elif AT_Command == "SET_AUTH_PASSWD":
                    main.SERIAL.write("AT+OK SET_AUTH_PASSWD\n")
                    value.putString("AUTH_PASSWD", SerialData[dex1+1, end - 1])
                elif AT_Command == "FORMAT_NVS":
                    main.SERIAL.write("AT+OK FORMAT_NVS\n")
                    nvs.erase()
                    nvs.init()
                    machine.reset()
                elif AT_Command == "PRINT_HEAP":
                    main.SERIAL.write("AT+OK PRINT_HEAP\n")
                    main.SERIAL.write(gc.mem_free())
                    main.SERIAL.write("Byte\n")
                elif AT_Command == "WHATTIMEISIT":
                    main.SERIAL.write("AT+OK WHATTIMEISIT\n")
                elif AT_Command == "REBOOT":
                    main.SERIAL.write("AT+OK REBOOT\n")
                    time.sleep(0.5)
                    machine.reset()
                else:
                    main.SERIAL.write("ERROR: Unknown command\n")