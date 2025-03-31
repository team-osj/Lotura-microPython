import machine
import main

def CH1SETVAR(SerialData, dex1, dexc, end):
    dexc = SerialData.indexOf(',')
    command = SerialData.substring(dex1+1, dexc)
    Number = SerialData.substring(dexc+1, end - 1)

    if command == "DeviceNo":
        string = f"CH1_DeviceNo : {Number}\n"
        main.SERIAL.write(string)
        main.preferences.putString("CH1_DeviceNo", str(Number))
    elif command == "Current_Wash":
        string = f"CH1_Curr_W : {Number}\n"
        main.SERIAL.write(string)
        var = float(Number)
        main.preferences.putFloat("CH1_Curr_W", var)
    elif command == "Flow_Wash":
        string = f"CH1_Flow_W : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putUInt("CH1_Flow_W", var)
    elif command == "Current_Dry":
        string = f"CH1_Curr_D : {Number}\n"
        main.SERIAL.write(string)
        var = float(Number)
        main.preferences.putFloat("CH1_Curr_D", var)
    elif command == "EndDelay_Wash":
        string = f"CH1_EndDelay_W : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putFloat("CH1_EndDelay_W", var)
    elif command == "EndDelay_Dry":
        string = f"CH1_EndDelay_D : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putUInt("CH1_EndDelay_D", var)
    elif command == "Enable":
        string = f"CH1_Enable : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putBool("CH1_Live", var)
    else:
        string = f"Command Not Found for : {command}\n"
        main.SERIAL.write(string)
    return 0

def CH2SETVAR(SerialData, dex1, dexc, end):
    dexc = SerialData.indexOf(',')
    command = SerialData.substring(dex1+1, dexc)
    Number = SerialData.substring(dexc+1, end - 1)

    if command == "DeviceNo":
        string = f"CH2_DeviceNo : {Number}\n"
        main.SERIAL.write(string)
        main.preferences.putString("CH2_DeviceNo", str(Number))
    elif command == "Current_Wash":
        string = f"CH2_Curr_W : {Number}\n"
        main.SERIAL.write(string)
        var = float(Number)
        main.preferences.putFloat("CH2_Curr_W", var)
    elif command == "Flow_Wash":
        string = f"CH2_Flow_W : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putUInt("CH2_Flow_W", var)
    elif command == "Current_Dry":
        string = f"CH2_Curr_D : {Number}\n"
        main.SERIAL.write(string)
        var = float(Number)
        main.preferences.putFloat("CH2_Curr_D", var)
    elif command == "EndDelay_Wash":
        string = f"CH2_EndDelay_W : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putFloat("CH2_EndDelay_W", var)
    elif command == "EndDelay_Dry":
        string = f"CH2_EndDelay_D : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putUInt("CH2_EndDelay_D", var)
    elif command == "Enable":
        string = f"CH2_Enable : {Number}\n"
        main.SERIAL.write(string)
        var = int(Number)
        main.preferences.putBool("CH2_Live", var)
    else:
        string = f"Command Not Found for : {command}\n"
        main.SERIAL.write(string)
    return 0