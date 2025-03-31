import machine
import main

def Flow1(): #CH1 유량센서 인터럽트
    main.CH1FlowFrequency += 1

def Flow2(): #CH2 유량센서 인터럽트
    main.CH2FlowFrequency += 1