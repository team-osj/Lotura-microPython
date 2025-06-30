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

# NVS storage simulation
def NvsGetString(key, default):
    try:
        with open(f"/nvs/{key}.txt", "r") as f:
            return f.read()
    except:
        return default

def NvsPutString(key, value):
    try:
        uos.mkdir("/nvs")
    except:
        pass
    with open(f"/nvs/{key}.txt", "w") as f:
        f.write(value)

def NvsGetFloat(key, default):
    try:
        with open(f"/nvs/{key}.txt", "r") as f:
            return float(f.read())
    except:
        return default

def NvsPutFloat(key, value):
    try:
        uos.mkdir("/nvs")
    except:
        pass
    with open(f"/nvs/{key}.txt", "w") as f:
        f.write(str(value))

def NvsGetUint(key, default):
    try:
        with open(f"/nvs/{key}.txt", "r") as f:
            return int(f.read())
    except:
        return default

def NvsPutUint(key, value):
    try:
        uos.mkdir("/nvs")
    except:
        pass
    with open(f"/nvs/{key}.txt", "w") as f:
        f.write(str(value))

def NvsGetBool(key, default):
    try:
        with open(f"/nvs/{key}.txt", "r") as f:
            return f.read() == "1"
    except:
        return default

def NvsPutBool(key, value):
    try:
        uos.mkdir("/nvs")
    except:
        pass
    with open(f"/nvs/{key}.txt", "w") as f:
        f.write("1" if value else "0")

# WebSocket client (simplified, using socket for HTTPS)
async def WebsocketConnect():
    global isPingFlag, lastPingMillis
    try:
        addr = socket.getaddrinfo(serverDomain, serverPort)[0][-1]
        s = socket.socket()
        s.connect(addr)
        # Simplified HTTPS handshake (MicroPython’s ussl is limited; consider external module)
        s = ussl.wrap_socket(s)
        headers = (
            f"GET {serverUrl} HTTP/1.1\r\n"
            f"Host: {serverDomain}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {ubinascii.b2a_base64(b'websocket').decode().strip()}\r\n"
            f"HWID: {serialNo}\r\n"
            f"CH1: {ch1DeviceNo}\r\n"
            f"CH2: {ch2DeviceNo}\r\n"
            f"ROOM: {roomNo}\r\n"
            f"Authorization: Basic {ubinascii.b2a_base64(authId + ':' + authPasswd).decode().strip()}\r\n\r\n"
        )
        s.write(headers.encode())
        response = s.readline()
        if b"101 Switching Protocols" in response:
            print("[WSc] Connected to WebSocket")
            isPingFlag = True
            lastPingMillis = utime.ticks_ms()
            if isModeDebug:
                if isCh1Live:
                    SendStatus(1, ch1CurrStatus)
                if isCh2Live:
                    SendStatus(2, ch2CurrStatus)
        return s
    except Exception as e:
        print(f"[WSc] Connection failed: {e}")
        return None

async def WebsocketLoop():
    global isPingFlag, lastPingMillis
    s = await WebsocketConnect()
    while s:
        try:
            data = s.read(1024)
            if data:
                await WebsocketEvent(data)
            if isPingFlag and utime.ticks_diff(utime.ticks_ms(), lastPingMillis) >= pingLateMillis:
                isPingFlag = False
                s.close()
                break
            await asyncio.sleep_ms(10)
        except:
            break
    if s:
        s.close()

async def WebsocketEvent(data):
    # Simplified WebSocket event handling
    try:
        payload = data.decode()
        print(f"[WSc] get text: {payload}")
        doc = ujson.loads(payload)
        if doc.get("title") == "GetData":
            status = {
                "title": "GetData",
                "debug": "No" if isModeDebug else "Yes",
                "ch1Mode": "Wash" if isCh1Mode else "Dry",
                "ch2Mode": "Wash" if isCh2Mode else "Dry",
                "ch1Status": "Not Working" if ch1CurrStatus else "Working",
                "ch2Status": "Not Working" if ch2CurrStatus else "Working",
                "ch1CurrW": ch1CurrW,
                "ch2CurrW": ch2CurrW,
                "ch1FlowW": ch1FlowW,
                "ch2FlowW": ch2FlowW,
                "ch1CurrD": ch1CurrD,
                "ch2CurrD": ch2CurrD,
                "ch1EndDelayW": ch1EndDelayW,
                "ch2EndDelayW": ch2EndDelayW,
                "ch1EndDelayD": ch1EndDelayD,
                "ch2EndDelayD": ch2EndDelayD,
                "ch1DeviceNo": ch1DeviceNo,
                "ch2DeviceNo": ch2DeviceNo,
                "ch1Current": ampsTrms1,
                "ch2Current": ampsTrms2,
                "ch1Flow": lHour1,
                "ch2Flow": lHour2,
                "ch1Drain": waterSensorData1,
                "ch2Drain": waterSensorData2,
                "wifiSsid": apSsid,
                "wifiRssi": staIf.status("rssi"),
                "wifiIp": staIf.ifconfig()[0],
                "mac": ubinascii.hexlify(staIf.config("mac")).decode(),
                "fwVer": buildDate
            }
            s = await WebsocketConnect()
            if s:
                s.write(ujson.dumps(status).encode())
    except Exception as e:
        print(f"[WSc] Error: {e}")

async def SendStatus(ch, status):
    if (ch == 1 and not isCh1Live) or (ch == 2 and not isCh2Live):
        return 1
    if staIf.isconnected():
        currStatus = {
            "title": "Update",
            "id": ch1DeviceNo if ch == 1 else ch2DeviceNo,
            "type": globals()[f"timeSendFlag{ch}"],
            "state": status
        }
        globals()[f"timeSendFlag{ch}"] = 0
        s = await WebsocketConnect()
        if s:
            s.write(ujson.dumps(currStatus).encode())
            return 0
    print("SendStatus Fail - No Server Connection")
    return 1

async def SendLog(ch, log):
    if (ch == 1 and not isCh1Live) or (ch == 2 and not isCh2Live):
        return 1
    if staIf.isconnected():
        logData = {
            "title": "Log",
            "id": ch1DeviceNo if ch == 1 else ch2DeviceNo,
            "log": log
        }
        s = await WebsocketConnect()
        if s:
            s.write(ujson.dumps(logData).encode())
            return 0
    print("SendLog Fail - No Server Connection")
    return 1

# HTML templates (from ok_html.h and manager_html.h)
okHtml = """
<!DOCTYPE html>
<html>
<head>
  <title>Firmware Update Success</title>
</head>
<body>
  <a href="/">Return</a>
</body>
</html>
"""

failedHtml = """
<!DOCTYPE html>
<html>
<head>
  <title>Firmware Update Fail</title>
</head>
<body>
  <a href="/">Return</a>
</body>
</html>
"""

managerHtml = """
<!DOCTYPE HTML>
<html>
<head>
  <title>%deviceName%</title>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {
      background-color: #f7f7f7;
    }
    #submit {
      width: 120px;
    }
    #edit_path {
      width: 250px;
    }
    #delete_path {
      width: 250px;
    }
    #spacer_50 {
      height: 50px;
    }
    #spacer_20 {
      height: 20px;
    }
    table {
      background-color: #dddddd;
      border-collapse: collapse;
      width: 650px;
    }
    td,
    th {
      border: 1px solid #dddddd;
      text-align: left;
      padding: 8px;
    }
    #first_td_th {
      width: 400px;
    }
    tr:nth-child(even) {
      background-color: #ffffff;
    }
    #format_notice {
      color: #ff0000;
    }
    #left_div {
      float: left;
      box-sizing: border-box;
      vertical-align: middle;
      display: inline-block;
    }
    #right_div {
      float: right;
      box-sizing: border-box;
      vertical-align: middle;
      display: inline-block;
    }
    #wrap_div {
      margin: auto;
      text-align: center;
    }
  </style>
  <script>
    function validateFormUpdate() {
      var inputElement = document.getElementById('update');
      var files = inputElement.files;
      if (files.length == 0) {
        alert("File Not Selected");
        return false;
      }
      var value = inputElement.value;
      var dotIndex = value.lastIndexOf(".") + 1;
      var valueExtension = value.substring(dotIndex);
    }
    function confirmFormat() {
      var text = "まじで...?www";
      if (confirm(text) == true) {
        return true;
      }
      else {
        return false;
      }
    }
    function callSetDefaultVal() {
      return true; // Simplified, as no specific validation is required
    }
  </script>
</head>
<body>
  <center>
    <h2>%deviceName%</h2>
    <div id="spacer_20"></div>
    <table>
      <td align="center" valign="top">
        <center>
          <fieldset style="width: 700px;background-color: #f7f7f7;">
            <legend>Device INFO</legend>
            <table>
              <tr>
                <th scope="col">WiFi SSID</th>
                <td>%apSsid%</td>
              </tr>
              <tr>
                <th scope="col">RSSI</th>
                <td>%wifiRssi% (%wifiQuality%)</td>
              </tr>
              <tr>
                <th scope="col">Device IP</th>
                <td>%wifiIp%</td>
              </tr>
              <tr>
                <th scope="col">MAC</th>
                <td>%mac%</td>
              </tr>
              <tr>
                <th scope="col">RoomNo</th>
                <td>%roomNo%</td>
              </tr>
              <tr>
                <th scope="col">CH1</th>
                <td>%ch1DeviceNo%</td>
                <th>Enable</th>
                <td>%isCh1Live%</td>
              </tr>
              <tr>
                <th scope="col">Mode</th>
                <td>%ch1Mode%</td>
                <th></th>
                <td></td>
              </tr>
              <tr>
                <th scope="col">C_W, Flow, C_D</th>
                <td>%ch1CurrW%</td>
                <td>%ch1FlowW%</td>
                <td>%ch1CurrD%</td>
              </tr>
              <tr>
                <th scope="col">EndDelay_W, D</th>
                <td>%ch1EndDelayW%</td>
                <td>%ch1EndDelayD%</td>
                <td></td>
              </tr>
              <tr>
                <th scope="col">Curr, Water, Flow</th>
                <td>%ampsTrms1%</td>
                <td>%waterSensorData1%</td>
                <td>%lHour1%</td>
              </tr>
              <tr>
                <th scope="col">CH2</th>
                <td>%ch2DeviceNo%</td>
                <th>Enable</th>
                <td>%isCh2Live%</td>
              </tr>
              <tr>
                <th scope="col">Mode</th>
                <td>%ch2Mode%</td>
                <th></th>
                <td></td>
              </tr>
              <tr>
                <th scope="col">C_W, Flow, C_D</th>
                <td>%ch2CurrW%</td>
                <td>%ch2FlowW%</td>
                <td>%ch2CurrD%</td>
              </tr>
              <tr>
                <th scope="col">EndDelay_W, D</th>
                <td>%ch2EndDelayW%</td>
                <td>%ch2EndDelayD%</td>
                <td></td>
              </tr>
              <tr>
                <th scope="col">Curr, Water, Flow</th>
                <td>%ampsTrms2%</td>
                <td>%waterSensorData2%</td>
                <td>%lHour2%</td>
              </tr>
              <tr>
                <th scope="col">Flash Size</th>
                <td>%flashSize% KiB</td>
              </tr>
              <tr>
                <th scope="col">Heap Memory</th>
                <td>%heap% KiB Left</td>
              </tr>
              <tr>
                <th scope="col">F/W Build Date</th>
                <td>%buildVer%</td>
              </tr>
            </table>
          </fieldset>
        </center>
      </td>
      <td align="center" valign="top">
        <center>
          <table>
            <tr>
              <td>
                <center>
                  <fieldset style="width:325px;background-color: #f7f7f7;">
                    <legend>WiFi Setting</legend>
                    <form method="POST" action="/wifi">
                      <p>
                        <input type="text" id="WiFi_SSID" name="wifiSsid" placeholder="SSID"><br>
                        <input type="text" id="WiFi_PASS" name="wifiPass" placeholder="Password"><br>
                      <div id="spacer_10"></div>
                      </p>
                      <input type="submit" value="Submit">
                    </form>
                  </fieldset>
                </center>
              </td>
              <td>
                <center>
                  <fieldset style="width:325px;background-color: #f7f7f7;">
                    <legend>HTTP AUTH Setting</legend>
                    <form method="POST" action="/auth">
                      <p>
                        <input type="text" id="AUTH_ID" name="authId" placeholder="ID"><br>
                        <input type="text" id="AUTH_PASSWD" name="authPasswd" placeholder="Password"><br>
                      <div id="spacer_10"></div>
                      </p>
                      <input type="submit" value="Submit">
                    </form>
                  </fieldset>
                </center>
              </td>
            </tr>
            <tr></tr>
            <tr>
              <td>
                <center>
                  <fieldset style="width:325px;height:100px;background-color: #f7f7f7;">
                    <legend>CH1_Setting</legend>
                    <form method="POST" action="/CH1">
                      <p>
                        <select name="CH1">
                          <option value="none" selected>Select Command</option>
                          <option value="DeviceNo">DeviceNo</option>
                          <option value="CurrentWash">CurrentWash</option>
                          <option value="FlowWash">FlowWash</option>
                          <option value="CurrentDry">CurrentDry</option>
                          <option value="EndDelayWash">EndDelayWash</option>
                          <option value="EndDelayDry">EndDelayDry</option>
                          <option value="Enable">Enable</option>
                        </select>
                        <input type="text" id="Command" name="value" placeholder="value"><br>
                      <div id="spacer_10"></div>
                      </p>
                      <input type="submit" value="Submit">
                    </form>
                  </fieldset>
                </center>
              </td>
              <td>
                <center>
                  <fieldset style="width:325px;height:100px;background-color: #f7f7f7;">
                    <legend>CH2_Setting</legend>
                    <form method="POST" action="/CH2">
                      <p>
                        <select name="CH2">
                          <option value="none" selected>Select Command</option>
                          <option value="DeviceNo">DeviceNo</option>
                          <option value="CurrentWash">CurrentWash</option>
                          <option value="FlowWash">FlowWash</option>
                          <option value="CurrentDry">CurrentDry</option>
                          <option value="EndDelayWash">EndDelayWash</option>
                          <option value="EndDelayDry">EndDelayDry</option>
                          <option value="Enable">Enable</option>
                        </select>
                        <input type="text" id="Command" name="value" placeholder="value"><br>
                      <div id="spacer_10"></div>
                      </p>
                      <input type="submit" value="Submit">
                    </form>
                  </fieldset>
                </center>
              </td>
            </tr>
          </table>
          <div id="spacer_20"></div>
          <fieldset style="width:700px;background-color: #f7f7f7;">
                  <legend>Room</legend>
                  <form method="POST" action="/roomno">
                      <input type="text" id="RoomNo" name="roomNo" placeholder="RoomNo"><br>
                    <div id="spacer_10"></div>
                    <input type="submit" value="Submit">
                  </form>
          </fieldset>
          <div id="spacer_20"></div>
          <fieldset style="width: 700px;background-color: #f7f7f7;">
            <legend>Firmware Update</legend>
            <div id="spacer_20"></div>
            <form method="POST" action="/update" enctype="multipart/form-data">
              <table>
                <tr>
                  <td id="first_td_th">
                    <input type="file" id="update" name="update">
                  </td>
                  <td>
                    <input type="submit" id="submit" value="Start" onclick="return validateFormUpdate()">
                  </td>
                </tr>
              </table>
            </form>
            <div id="spacer_20"></div>
          </fieldset>
          <div id="spacer_20"></div>
          <fieldset style="width: 700px;background-color: #f7f7f7;">
            <legend>Load Variable From NVS</legend>
            <form method="GET" action="/SetDefaultVal" enctype="multipart/form-data">
              <input type="submit" id="submit" value="LOAD" onclick="return callSetDefaultVal()">
            </form>
          </fieldset>
          <div id="spacer_20"></div>
          <fieldset style="width: 700px;background-color: #f7f7f7;">
            <legend>Device Reboot</legend>
            <form method="GET" action="/reboot" enctype="multipart/form-data">
              <input type="submit" id="submit" value="REBOOT" onclick="return confirmFormat()">
            </form>
          </fieldset>
        </center>
      </td>
    </table>
  </center>
  <iframe style="display:none" name="self_page"></iframe>
</body>
</html>
"""

# Processor for HTML template
def Processor(template, vars):
    for key, value in vars.items():
        template = template.replace(f"%{key}%", str(value))
    return template

# Web server
async def HandleClient(reader, writer):
    global isRebooting
    try:
        request = (await reader.read(1024)).decode()
        headers = request.split("\r\n")
        firstLine = headers[0]
        method, path, _ = firstLine.split(" ")
        
        # Basic authentication
        auth = None
        for header in headers:
            if header.startswith("Authorization: Basic "):
                auth = ubinascii.a2b_base64(header[20:]).decode().split(":")
                break
        if auth != [authId, authPasswd]:
            writer.write(b"HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Secure Area\"\r\n\r\n")
            await writer.drain()
            return

        vars = {
            "deviceName": deviceName,
            "apSsid": apSsid,
            "apPasswd": apPasswd,
            "wifiRssi": staIf.status("rssi") if staIf.isconnected() else "N/A",
            "wifiQuality": "WiFi Not Connected" if not staIf.isconnected() else (
                "Very Good" if staIf.status("rssi") > -40 else
                "Good" if staIf.status("rssi") > -60 else
                "Weak" if staIf.status("rssi") > -70 else "Poor"
            ),
            "wifiIp": staIf.ifconfig()[0] if staIf.isconnected() else "N/A",
            "mac": ubinascii.hexlify(staIf.config("mac")).decode(),
            "roomNo": roomNo,
            "flashSize": str(uos.statvfs("/")[0] * uos.statvfs("/")[2] // 1024),
            "heap": str(gc.mem_free() // 1024),
            "buildVer": buildDate,
            "ch1DeviceNo": ch1DeviceNo,
            "isCh1Live": "Yes" if isCh1Live else "No",
            "ch1Mode": "Wash" if isCh1Mode else "Dry",
            "ch1CurrW": ch1CurrW,
            "ch1FlowW": ch1FlowW,
            "ch1CurrD": ch1CurrD,
            "ch1EndDelayW": ch1EndDelayW,
            "ch1EndDelayD": ch1EndDelayD,
            "ampsTrms1": ampsTrms1,
            "waterSensorData1": waterSensorData1,
            "lHour1": lHour1,
            "ch2DeviceNo": ch2DeviceNo,
            "isCh2Live": "Yes" if isCh2Live else "No",
            "ch2Mode": "Wash" if isCh2Mode else "Dry",
            "ch2CurrW": ch2CurrW,
            "ch2FlowW": ch2FlowW,
            "ch2CurrD": ch2CurrD,
            "ch2EndDelayW": ch2EndDelayW,
            "ch2EndDelayD": ch2EndDelayD,
            "ampsTrms2": ampsTrms2,
            "waterSensorData2": waterSensorData2,
            "lHour2": lHour2
        }

        if path == "/":
            response = Processor(managerHtml, vars)
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + response.encode())
        elif path == "/wifi" and method == "POST":
            data = headers[-1]
            params = ParseFormData(data)
            if "wifiSsid" in params:
                NvsPutString("apSsid", params["wifiSsid"])
                print(f"SSID set to: {params['wifiSsid']}")
            if "wifiPass" in params:
                NvsPutString("apPasswd", params["wifiPass"])
                print(f"Password set to: {params['wifiPass']}")
            writer.write(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
        elif path == "/auth" and method == "POST":
            data = headers[-1]
            params = ParseFormData(data)
            if "authId" in params:
                global authId
                authId = params["authId"]
                NvsPutString("authId", authId)
                print(f"authId: {authId}")
            if "authPasswd" in params:
                global authPasswd
                authPasswd = params["authPasswd"]
                NvsPutString("authPasswd", authPasswd)
                print(f"authPasswd: {authPasswd}")
            writer.write(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
        elif path == "/CH1" and method == "POST":
            data = headers[-1]
            params = ParseFormData(data)
            if "CH1" in params and "value" in params:
                command, value = params["CH1"], params["value"]
                Ch1SetVar(command, value)
            writer.write(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
        elif path == "/CH2" and method == "POST":
            data = headers[-1]
            params = ParseFormData(data)
            if "CH2" in params and "value" in params:
                command, value = params["CH2"], params["value"]
                Ch2SetVar(command, value)
            writer.write(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
        elif path == "/roomno" and method == "POST":
            data = headers[-1]
            params = ParseFormData(data)
            if "roomNo" in params:
                global roomNo
                roomNo = params["roomNo"]
                NvsPutString("roomNo", roomNo)
                print(f"roomNo: {roomNo}")
            writer.write(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")

            
        elif path == "/update" and method == "POST":
            # Simplified OTA (write to file, reboot to apply)
            data = headers[-1]
            if "update" in data:
                with open("/update.bin", "wb") as f:
                    f.write(data)  # Simplified; real OTA needs chunked reading
                isRebooting = True
                response = okHtml if isRebooting else failedHtml
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n" + response.encode())
            else:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")


        elif path == "/reboot" and method == "GET":
            writer.write(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
            await writer.drain()
            machine.reset()
        elif path == "/SetDefaultVal" and method == "GET":
            SetDefaultVal()
            writer.write(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
        else:
            writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
        
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Web server error: {e}")

def ParseFormData(data):
    params = {}
    for pair in data.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[key] = value
    return params

async def WebServer():
    server = await asyncio.start_server(HandleClient, "0.0.0.0", 80)
    await server.serve_forever()
