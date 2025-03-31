import machine
import ujson
import time
import main
import send

def DryerStatusJudgment(ampsTRMS, cnt, m, prevMillisEnd, ChannelNum):
    if ChannelNum == 1 and ampsTRMS < main.CH1CurrD and main.CH1JsonLogFlag:
        if main.CH1JsonLogFlagC == 1:
            main.CH1JsonLogFlagC = 0
            CH1JsonLogCntString = str(main.CH1JsonLogCnt)
            main.CH1JsonLog[CH1JsonLogCntString]["t"] =  - main.CH1JsonLogMillis
            main.CH1JsonLog[CH1JsonLogCntString]["n"] = "C"
            main.CH1JsonLog[CH1JsonLogCntString]["s"] = 0
            if main.CH1JsonLogCnt % 100 == 0:
                CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                main.CH1JsonLog.clear()
                send.SendLog(1, CH1JsonLogData)
            main.CH1JsonLogCnt += 1

    if ChannelNum == 2 and ampsTRMS < main.CH2CurrD and main.CH2JsonLogFlag:
        if main.CH2JsonLogFlagC == 1:
            main.CH2JsonLogFlagC = 0
            CH2JsonLogCntString = str(main.CH2JsonLogCnt)
            main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
            main.CH2JsonLog[CH2JsonLogCntString]["n"] = "C"
            main.CH2JsonLog[CH2JsonLogCntString]["s"] = 0
            if main.CH2JsonLogCnt % 100 == 0:
                CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                main.CH2JsonLog.clear()
                send.SendLog(1, CH2JsonLogData)
            main.CH2JsonLogCnt += 1
    if ChannelNum == 1 and ampsTRMS > main.CH1CurrD:
        if main.CH1JsonLogFlag:
            if main.CH1JsonLogFlagC == 0:
                main.CH1JsonLogFlagC = 1
                CH1JsonLogCntString = str(main.CH1JsonLogCnt)
                main.CH1JsonLog[CH1JsonLogCntString]["t"] = time.ticks_ms() - main.CH1JsonLogMillis
                main.CH1JsonLog[CH1JsonLogCntString]["n"] = "C"
                main.CH1JsonLog[CH1JsonLogCntString]["s"] = 1
                if main.CH1JsonLogCnt % 100 == 0:
                    CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                    main.CH1JsonLog.clear()
                    send.SendLog(1, CH1JsonLogData)
                main.CH1JsonLogCnt += 1
        if cnt == 1:
            main.CH1TimeSendFlag = 1
            main.CH1JsonLogFlag = 1
            main.CH1JsonLogCnt = 1
            main.CH1JsonLogMillis = time.ticks_ms()
            local_time = ""
            main.CH1JsonLog["START"]["local_time"] = local_time

            main.CH1Cnt = 0
            main.PIN_CH1_LED.value(1)
            main.CH1CurrStatus = 0
            string = f"CH1 Dryer Started\n"
            main.SERIAL.write(string)
            send.SendStatus(ChannelNum, 0)
        main.CH1M = 1
    elif ChannelNum == 2 and ampsTRMS > main.CH2CurrD:
        if main.CH2JsonLogFlag:
            if main.CH2JsonLogFlagC == 0:
                main.CH2JsonLogFlagC = 1
                CH2JsonLogCntString = str(main.CH2JsonLogCnt)
                main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
                main.CH2JsonLog[CH2JsonLogCntString]["n"] = "C"
                main.CH2JsonLog[CH2JsonLogCntString]["s"] = 1
                if main.CH2JsonLogCnt % 100 == 0:
                    CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                    main.CH2JsonLog.clear()
                    send.SendLog(2, CH2JsonLogData)
                main.CH2JsonLogCnt += 1
        if cnt == 1:
            main.CH2TimeSendFlag = 1
            main.CH2JsonLogFlag = 1
            main.CH2JsonLogCnt = 1
            main.CH2JsonLogMillis = time.ticks_ms()
            local_time = ""
            main.CH2JsonLog["START"]["local_time"] = local_time

            main.CH2Cnt = 0
            main.PIN_CH2_LED.value(1)
            main.CH2CurrStatus = 0
            string = f"CH2 Dryer Started\n"
            main.SERIAL.write(string)
            send.SendStatus(ChannelNum, 0)
        main.CH2M = 1
    else:
        if prevMillisEnd > time.ticks_ms():
            prevMillisEnd = time.ticks_ms()
        if m:
            if ChannelNum == 1:
                main.CH1PrevMillisEnd = time.ticks_ms()
            if ChannelNum == 2:
                main.CH2PrevMillisEnd = time.ticks_ms()
            if ChannelNum == 1:
                main.CH1M = 0
            if ChannelNum == 2:
                main.CH2M = 0
        elif ChannelNum == 1 and time.ticks_ms() - prevMillisEnd >= main.CH1EndDelayD:
            main.CH1TimeSendFlag = 1

            main.CH1JsonLogFlagC = 0
            main.CH1JsonLogFlag = 0

            local_time = ""
            main.CH1JsonLog["END"]["local_time"] = local_time

            CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
            main.CH1JsonLog.clear()
            main.SERIAL.write("CH1 Dryer Ended\n")
            send.SendStatus(1, 1)
            send.SendLog(1, CH1JsonLogData)
            main.CH1Cnt = 1
            main.PIN_CH1_LED.value(0)
            main.CH1CurrStatus = 1
        elif ChannelNum == 2 and time.ticks_ms() - prevMillisEnd >= main.CH2EndDelayD:
            main.CH2TimeSendFlag = 1
            
            main.CH2JsonLogFlagC = 0
            main.CH2JsonLogFlag = 0

            local_time = ""
            main.CH2JsonLog["END"]["local_time"] = local_time

            CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
            main.CH2JsonLog.clear()
            main.SERIAL.write("CH2 Dryer Ended\n")
            send.SendStatus(2, 1)
            send.SendLog(2, CH2JsonLogData)
            main.CH2Cnt = 1
            main.PIN_CH2_LED.value(0)
            main.CH1CurrStatus = 1

def StatusJudgment(ampsTRMS, waterSensorData, LHour, cnt, m, prevMillisEnd, ChannelNum):
    if ChannelNum == 1 and (ampsTRMS > main.CH1CurrW or waterSensorData or LHour > main.CH1FlowW) and main.CH1SeCnt == 0:
        main.CH1SeCnt = 1
        main.CH1SePrevMillis = time.ticks_ms()
    if ChannelNum == 1 and (ampsTRMS < main.CH1CurrW and not waterSensorData or LHour < main.CH1FlowW) and main.CH1SeCnt == 1:
        main.CH1Cnt = 0
    if ChannelNum == 2 and (ampsTRMS > main.CH2CurrW or waterSensorData or LHour > main.CH2FlowW) and main.CH2SeCnt == 0:
        main.CH2SeCnt = 1
        main.CH2SePrevMillis = time.ticks_ms()
    if ChannelNum == 2 and (ampsTRMS < main.CH2CurrW and not waterSensorData or LHour < main.CH2FlowW) and main.CH2SeCnt == 1:
        main.CH2Cnt = 0
    
    if ChannelNum == 1:
        if main.CH1JsonLogFlag:
            if ampsTRMS > main.CH1CurrW and main.CH1JsonLogFlagC == 0:
                main.CH1JsonLogFlagC == 1
                CH1JsonLogCntString = str(main.CH1JsonLogCnt)
                main.CH1JsonLog[CH1JsonLogCntString]["t"] = time.ticks_ms() - main.CH1JsonLogMillis
                main.CH1JsonLog[CH1JsonLogCntString]["n"] = "C"
                main.CH1JsonLog[CH1JsonLogCntString]["s"] = 1
                if main.CH1JsonLogCnt % 100 == 0:
                    CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                    main.CH1JsonLog.clear()
                    send.SendLog(1, CH1JsonLogData)
                main.CH1JsonLogCnt += 1
            if ampsTRMS < main.CH1CurrW and main.CH1JsonLogFlagC == 1:
                main.CH1JsonLogFlagC = 0
                CH1JsonLogCntString = str(main.CH1JsonLogCnt)
                main.CH1JsonLog[CH1JsonLogCntString]["t"] = time.ticks_ms() - main.CH1JsonLogMillis
                main.CH1JsonLog[CH1JsonLogCntString]["n"] = "C"
                main.CH1JsonLog[CH1JsonLogCntString]["s"] = 0
                if main.CH1JsonLogCnt % 100 == 0:
                    CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                    main.CH1JsonLog.clear()
                    send.SendLog(1, CH1JsonLogData)
                main.CH1JsonLogCnt += 1

            if ampsTRMS > main.CH1CurrW and main.CH1JsonLogFlagF == 0:
                main.CH1JsonLogFlagF == 1
                CH1JsonLogCntString = str(main.CH1JsonLogCnt)
                main.CH1JsonLog[CH1JsonLogCntString]["t"] = time.ticks_ms() - main.CH1JsonLogMillis
                main.CH1JsonLog[CH1JsonLogCntString]["n"] = "F"
                main.CH1JsonLog[CH1JsonLogCntString]["s"] = 1
                if main.CH1JsonLogCnt % 100 == 0:
                    CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                    main.CH1JsonLog.clear()
                    send.SendLog(1, CH1JsonLogData)
                main.CH1JsonLogCnt += 1
            if ampsTRMS < main.CH1CurrW and main.CH1JsonLogFlagF == 1:
                main.CH1JsonLogFlagF = 0
                CH1JsonLogCntString = str(main.CH1JsonLogCnt)
                main.CH1JsonLog[CH1JsonLogCntString]["t"] = time.ticks_ms() - main.CH1JsonLogMillis
                main.CH1JsonLog[CH1JsonLogCntString]["n"] = "F"
                main.CH1JsonLog[CH1JsonLogCntString]["s"] = 0
                if main.CH1JsonLogCnt % 100 == 0:
                    CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                    main.CH1JsonLog.clear()
                    send.SendLog(1, CH1JsonLogData)
                main.CH1JsonLogCnt += 1
            
            if waterSensorData and main.CH1JsonLogFlagW == 0:
                main.CH1JsonLogFlagW == 1
                CH1JsonLogCntString = str(main.CH1JsonLogCnt)
                main.CH1JsonLog[CH1JsonLogCntString]["t"] = time.ticks_ms() - main.CH1JsonLogMillis
                main.CH1JsonLog[CH1JsonLogCntString]["n"] = "W"
                main.CH1JsonLog[CH1JsonLogCntString]["s"] = 1
                if main.CH1JsonLogCnt % 100 == 0:
                    CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                    main.CH1JsonLog.clear()
                    send.SendLog(1, CH1JsonLogData)
                main.CH1JsonLogCnt += 1
            if not waterSensorData and main.CH1JsonLogFlagW == 1:
                main.CH1JsonLogFlagW = 0
                CH1JsonLogCntString = str(main.CH1JsonLogCnt)
                main.CH1JsonLog[CH1JsonLogCntString]["t"] = time.ticks_ms() - main.CH1JsonLogMillis
                main.CH1JsonLog[CH1JsonLogCntString]["n"] = "W"
                main.CH1JsonLog[CH1JsonLogCntString]["s"] = 0
                if main.CH1JsonLogCnt % 100 == 0:
                    CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
                    main.CH1JsonLog.clear()
                    send.SendLog(1, CH1JsonLogData)
                main.CH1JsonLogCnt += 1
            
    if ChannelNum == 2:
        if main.CH2JsonLogFlag:
            if ampsTRMS > main.CH2CurrW and main.CH2JsonLogFlagC == 0:
                main.CH2JsonLogFlagC == 1
                CH2JsonLogCntString = str(main.CH2JsonLogCnt)
                main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
                main.CH2JsonLog[CH2JsonLogCntString]["n"] = "C"
                main.CH2JsonLog[CH2JsonLogCntString]["s"] = 1
                if main.CH2JsonLogCnt % 100 == 0:
                    CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                    main.CH2JsonLog.clear()
                    send.SendLog(2, CH2JsonLogData)
                main.CH2JsonLogCnt += 1
            if ampsTRMS < main.CH1CurrW and main.CH2JsonLogFlagC == 1:
                main.CH2JsonLogFlagC = 0
                CH2JsonLogCntString = str(main.CH2JsonLogCnt)
                main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
                main.CH2JsonLog[CH2JsonLogCntString]["n"] = "C"
                main.CH2JsonLog[CH2JsonLogCntString]["s"] = 0
                if main.CH2JsonLogCnt % 100 == 0:
                    CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                    main.CH2JsonLog.clear()
                    send.SendLog(2, CH2JsonLogData)
                main.CH2JsonLogCnt += 1

            if ampsTRMS > main.CH2CurrW and main.CH2JsonLogFlagF == 0:
                main.CH2JsonLogFlagF == 1
                CH2JsonLogCntString = str(main.CH2JsonLogCnt)
                main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
                main.CH2JsonLog[CH2JsonLogCntString]["n"] = "F"
                main.CH2JsonLog[CH2JsonLogCntString]["s"] = 1
                if main.CH2JsonLogCnt % 100 == 0:
                    CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                    main.CH2JsonLog.clear()
                    send.SendLog(1, CH2JsonLogData)
                main.CH2JsonLogCnt += 1
            if ampsTRMS < main.CH2CurrW and main.CH2JsonLogFlagF == 1:
                main.CH2JsonLogFlagF = 0
                CH2JsonLogCntString = str(main.CH2JsonLogCnt)
                main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
                main.CH2JsonLog[CH2JsonLogCntString]["n"] = "F"
                main.CH2JsonLog[CH2JsonLogCntString]["s"] = 0
                if main.CH2JsonLogCnt % 100 == 0:
                    CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                    main.CH2JsonLog.clear()
                    send.SendLog(2, CH2JsonLogData)
                main.CH2JsonLogCnt += 1
            
            if waterSensorData and main.CH2JsonLogFlagW == 0:
                main.CH2JsonLogFlagW == 1
                CH2JsonLogCntString = str(main.CH2JsonLogCnt)
                main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
                main.CH2JsonLog[CH2JsonLogCntString]["n"] = "W"
                main.CH2JsonLog[CH2JsonLogCntString]["s"] = 1
                if main.CH2JsonLogCnt % 100 == 0:
                    CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                    main.CH2JsonLog.clear()
                    send.SendLog(2, CH2JsonLogData)
                main.CH2JsonLogCnt += 1
            if not waterSensorData and main.CH2JsonLogFlagW == 1:
                main.CH2JsonLogFlagW = 0
                CH2JsonLogCntString = str(main.CH2JsonLogCnt)
                main.CH2JsonLog[CH2JsonLogCntString]["t"] = time.ticks_ms() - main.CH2JsonLogMillis
                main.CH2JsonLog[CH2JsonLogCntString]["n"] = "W"
                main.CH2JsonLog[CH2JsonLogCntString]["s"] = 0
                if main.CH2JsonLogCnt % 100 == 0:
                    CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
                    main.CH2JsonLog.clear()
                    send.SendLog(2, CH2JsonLogData)
                main.CH2JsonLogCnt += 1

    if ChannelNum == 1 and time.ticks_ms() - main.CH1SePrevMillis >= 500 and main.CH1SeCnt == 1:
        if cnt == 1:
            main.CH1TimeSendFlag = 1
            main.CH1JsonLogFlag = 1
            main.CH1JsonLogCnt = 1
            main.CH1JsonLogMillis = time.ticks_ms()

            local_time = ""
            main.CH1JsonLog["START"]["local_time"] = local_time

            main.CH1SeCnt = 0
            main.CH1Cnt = 0
            main.PIN_CH1_LED.value(1)
            string = f"CH {ChannelNum} Washer Started\n"
            main.SERIAL.write(string)
            send.SendStatus(1, 0)
        main.CH1M = 1
    if ChannelNum == 2 and time.ticks_ms() - main.CH2SePrevMillis >= 500 and main.CH2SeCnt == 1:
        if cnt == 1:
            main.CH2TimeSendFlag = 1
            main.CH2JsonLogFlag = 1
            main.CH2JsonLogCnt = 1
            main.CH2JsonLogMillis = time.ticks_ms()

            local_time = ""
            main.CH2JsonLog["START"]["local_time"] = local_time

            main.CH2SeCnt = 0
            main.CH2Cnt = 0
            main.PIN_CH2_LED.value(1)
            main.CH2CurrStatus = 0
            string = f"CH {ChannelNum} Washer Started\n"
            main.SERIAL.write(string)
            send.SendStatus(2, 0)
        main.CH2M = 1
    else:
        if prevMillisEnd > time.ticks_ms():
            prevMillisEnd = time.ticks_ms()
        if m:
            if ChannelNum == 1:
                main.CH1PrevMillisEnd = time.ticks_ms()
            if ChannelNum == 2:
                main.CH2PrevMillisEnd = time.ticks_ms()
            if ChannelNum == 1:
                main.CH1M = 0
            if ChannelNum == 2:
                main.CH2M = 0

        #CH1 세탁기 동작 종료
        elif ChannelNum == 1 and time.ticks_ms() - prevMillisEnd >= main.CH1EndDelayW:
            main.CH1TimeSendFlag = 1

            main.CH1JsonLogFlagC = 0
            main.CH1JsonLogFlagF = 0
            main.CH1JsonLogFlagW = 0
            main.CH1JsonLogFlag = 0

            local_time = ""
            main.CH1JsonLog["END"]["local_time"] = local_time

            CH1JsonLogData = ujson.dumps(main.CH1JsonLog)
            main.CH1JsonLog.clear()
            main.SERIAL.write("CH1 Washer Ended\n")
            send.SendStatus(1, 1)
            send.SendLog(1, CH1JsonLogData)
            main.CH1Cnt = 1
            main.PIN_CH1_LED.value(0)
            main.CH1CurrStatus = 1

        #CH2 세탁기 동작 종료
        elif ChannelNum == 2 and time.ticks_ms() - prevMillisEnd >= main.CH2EndDelayW:
            main.CH2TimeSendFlag = 1

            main.CH2JsonLogFlagC = 0
            main.CH2JsonLogFlagF = 0
            main.CH2JsonLogFlagW = 0
            main.CH2JsonLogFlag = 0

            local_time = ""
            main.CH2JsonLog["END"]["local_time"] = local_time

            CH2JsonLogData = ujson.dumps(main.CH2JsonLog)
            main.CH2JsonLog.clear()
            main.SERIAL.write("CH2 Washer Ended\n")
            send.SendStatus(2, 1)
            send.SendLog(2, CH2JsonLogData)
            main.CH2Cnt = 1
            main.PIN_CH2_LED.value(0)
            main.CH2CurrStatus = 1