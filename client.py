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

def WiFiGotIP():

def WiFiStationDisconnected():

def NetworkInfo():