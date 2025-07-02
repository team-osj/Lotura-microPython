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

# Flow sensor interrupts
def Flow1(pin):
    global flowFrequency1
    flowFrequency1 += 1

def Flow2(pin):
    global flowFrequency2
    flowFrequency2 += 1

flow1.irq(trigger=Pin.IRQ_FALLING, handler=Flow1)
flow2.irq(trigger=Pin.IRQ_FALLING, handler=Flow2)

# Current measurement (simulating EmonLib)
def CalcIrms(adcPin, calibration):
    samples = 1480
    total = 0.0
    for _ in range(samples):
        value = adcPin.read()
        total += (value - 2048) ** 2  # Assuming 12-bit ADC, centered at 2048
        utime.sleep_us(100)
    irms = math.sqrt(total / samples) * calibration
    return irms

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

# AT command handler
async def HandleSerial():
    while True:
        if sys.stdin in uasyncio.select([sys.stdin])[0]:
            line = sys.stdin.readline().strip()
            dex = line.find("+")
            dex1 = line.find('"')
            end = len(line)
            if dex != -1 and dex1 != -1:
                atCommand = line[dex+1:dex1]
                if atCommand == "HELP":
                    print("AT+OK HELP")
                elif atCommand == "UPDATE":
                    print("AT+OK UPDATE")
                elif atCommand == "CH1_SETVAR":
                    print("AT+OK CH1_SETVAR")
                    Ch1SetVar(line[dex1+1:end-1].split(",")[0], line[dex1+1:end-1].split(",")[1])
                elif atCommand == "CH2_SETVAR":
                    print("AT+OK CH2_SETVAR")
                    Ch2SetVar(line[dex1+1:end-1].split(",")[0], line[dex1+1:end-1].split(",")[1])
                elif atCommand == "NETWORK_INFO":
                    print("AT+OK NETWORK_INFO")
                    NetworkInfo()
                elif atCommand == "SETAP_SSID":
                    print("AT+OK SETAP_SSID")
                    NvsPutString("apSsid", line[dex1+1:end-1])
                elif atCommand == "SETAP_PASSWD":
                    print("AT+OK SETAP_PASSWD")
                    NvsPutString("apPasswd", line[dex1+1:end-1])
                elif atCommand == "SET_SERIALNO":
                    print("AT+OK SET_SERIALNO")
                    NvsPutString("serialNo", line[dex1+1:end-1])
                elif atCommand == "SET_AUTH_ID":
                    print("AT+OK SET_AUTH_ID")
                    NvsPutString("authId", line[dex1+1:end-1])
                elif atCommand == "SET_AUTH_PASSWD":
                    print("AT+OK SET_AUTH_PASSWD")
                    NvsPutString("authPasswd", line[dex1+1:end-1])
                elif atCommand == "FORMAT_NVS":
                    print("AT+OK FORMAT_NVS")
                    try:
                        uos.remove("/nvs")
                    except:
                        pass
                    machine.reset()
                elif atCommand == "PRINT_HEAP":
                    print("AT+OK PRINT_HEAP")
                    print(f"{gc.mem_free()} Byte")
                elif atCommand == "REBOOT":
                    print("AT+OK REBOOT")
                    await asyncio.sleep_ms(500)
                    machine.reset()
                else:
                    print("ERROR: Unknown command")
        await asyncio.sleep_ms(10)

def Ch1SetVar(command, value):
    global ch1DeviceNo, ch1CurrW, ch1FlowW, ch1CurrD, ch1EndDelayW, ch1EndDelayD, isCh1Live
    print(f"ch1{command}: {value}")
    if command == "DeviceNo":
        ch1DeviceNo = value
        NvsPutString("ch1DeviceNo", value)
    elif command == "CurrentWash":
        ch1CurrW = float(value)
        NvsPutFloat("ch1CurrW", ch1CurrW)
    elif command == "FlowWash":
        ch1FlowW = int(value)
        NvsPutUint("ch1FlowW", ch1FlowW)
    elif command == "CurrentDry":
        ch1CurrD = float(value)
        NvsPutFloat("ch1CurrD", ch1CurrD)
    elif command == "EndDelayWash":
        ch1EndDelayW = int(value) * 10000
        NvsPutUint("ch1EndDelayW", ch1EndDelayW)
    elif command == "EndDelayDry":
        ch1EndDelayD = int(value) * 1000
        NvsPutUint("ch1EndDelayD", ch1EndDelayD)
    elif command == "Enable":
        isCh1Live = bool(int(value))
        NvsPutBool("isCh1Live", isCh1Live)
    else:
        print(f"Command Not Found for: {command}")

def Ch2SetVar(command, value):
    global ch2DeviceNo, ch2CurrW, ch2FlowW, ch2CurrD, ch2EndDelayW, ch2EndDelayD, isCh2Live
    print(f"ch2{command}: {value}")
    if command == "DeviceNo":
        ch2DeviceNo = value
        NvsPutString("ch2DeviceNo", value)
    elif command == "CurrentWash":
        ch2CurrW = float(value)
        NvsPutFloat("ch2CurrW", ch2CurrW)
    elif command == "FlowWash":
        ch2FlowW = int(value)
        NvsPutUint("ch2FlowW", ch2FlowW)
    elif command == "CurrentDry":
        ch2CurrD = float(value)
        NvsPutFloat("ch2CurrD", ch2CurrD)
    elif command == "EndDelayWash":
        ch2EndDelayW = int(value) * 10000
        NvsPutUint("ch2EndDelayW", ch2EndDelayW)
    elif command == "EndDelayDry":
        ch2EndDelayD = int(value) * 1000
        NvsPutUint("ch2EndDelayD", ch2EndDelayD)
    elif command == "Enable":
        isCh2Live = bool(int(value))
        NvsPutBool("isCh2Live", isCh2Live)
    else:
        print(f"Command Not Found for: {command}")

def DryerStatusJudgment(ampsTrms, cnt, m, previousMillisEnd, channelNum):
    global jsonLogFlag1, jsonLogFlag2, jsonLogFlag1C, jsonLogFlag2C
    global jsonLogCnt1, jsonLogCnt2, jsonLogMillis1, jsonLogMillis2
    global ch1Cnt, ch2Cnt, ch1CurrStatus, ch2CurrStatus, m1, m2
    global timeSendFlag1, timeSendFlag2

    if channelNum == 1 and ampsTrms < ch1CurrD and jsonLogFlag1:
        if jsonLogFlag1C == 1:
            jsonLogFlag1C = 0
            jsonLog1[str(jsonLogCnt1)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                "n": "C",
                "s": 0
            }
            if jsonLogCnt1 % 100 == 0:
                jsonLogData1 = ujson.dumps(jsonLog1)
                jsonLog1.clear()
                SendLog(1, jsonLogData1)
            jsonLogCnt1 += 1
    elif channelNum == 2 and ampsTrms < ch2CurrD and jsonLogFlag2:
        if jsonLogFlag2C == 1:
            jsonLogFlag2C = 0
            jsonLog2[str(jsonLogCnt2)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                "n": "C",
                "s": 0
            }
            if jsonLogCnt2 % 100 == 0:
                jsonLogData2 = ujson.dumps(jsonLog2)
                jsonLog2.clear()
                SendLog(2, jsonLogData2)
            jsonLogCnt2 += 1

    if channelNum == 1 and ampsTrms > ch1CurrD:
        if jsonLogFlag1:
            if jsonLogFlag1C == 0:
                jsonLogFlag1C = 1
                jsonLog1[str(jsonLogCnt1)] = {
                    "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                    "n": "C",
                    "s": 1
                }
                if jsonLogCnt1 % 100 == 0:
                    jsonLogData1 = ujson.dumps(jsonLog1)
                    jsonLog1.clear()
                    SendLog(1, jsonLogData1)
                jsonLogCnt1 += 1
        if cnt == 1:
            timeSendFlag1 = 1
            jsonLogFlag1 = 1
            jsonLogCnt1 = 1
            jsonLogMillis1 = utime.ticks_ms()
            jsonLog1["START"] = {"local_time": ""}
            ch1Cnt = 0
            ch1Led.value(1)
            ch1CurrStatus = 0
            print(f"CH{channelNum} Dryer Started")
            SendStatus(channelNum, 0)
        m1 = 1
    elif channelNum == 2 and ampsTrms > ch2CurrD:
        if jsonLogFlag2:
            if jsonLogFlag2C == 0:
                jsonLogFlag2C = 1
                jsonLog2[str(jsonLogCnt2)] = {
                    "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                    "n": "C",
                    "s": 1
                }
                if jsonLogCnt2 % 100 == 0:
                    jsonLogData2 = ujson.dumps(jsonLog2)
                    jsonLog2.clear()
                    SendLog(2, jsonLogData2)
                jsonLogCnt2 += 1
        if cnt == 1:
            timeSendFlag2 = 1
            jsonLogFlag2 = 1
            jsonLogCnt2 = 1
            jsonLogMillis2 = utime.ticks_ms()
            jsonLog2["START"] = {"local_time": ""}
            ch2Cnt = 0
            ch2Led.value(1)
            ch2CurrStatus = 0
            print(f"CH{channelNum} Dryer Started")
            SendStatus(channelNum, 0)
        m2 = 1
    else:
        if previousMillisEnd > utime.ticks_ms():
            previousMillisEnd = utime.ticks_ms()
        if m:
            if channelNum == 1:
                globals()["previousMillisEnd1"] = utime.ticks_ms()
                m1 = 0
            if channelNum == 2:
                globals()["previousMillisEnd2"] = utime.ticks_ms()
                m2 = 0
        elif cnt:
            pass
        elif channelNum == 1 and utime.ticks_diff(utime.ticks_ms(), previousMillisEnd) >= ch1EndDelayD:
            timeSendFlag1 = 1
            jsonLogFlag1C = 0
            jsonLogFlag1 = 0
            jsonLog1["END"] = {"local_time": ""}
            jsonLogData1 = ujson.dumps(jsonLog1)
            jsonLog1.clear()
            print("CH1 Dryer Ended")
            SendStatus(1, 1)
            SendLog(1, jsonLogData1)
            ch1Cnt = 1
            ch1Led.value(0)
            ch1CurrStatus = 1
        elif channelNum == 2 and utime.ticks_diff(utime.ticks_ms(), previousMillisEnd) >= ch2EndDelayD:
            timeSendFlag2 = 1
            jsonLogFlag2C = 0
            jsonLogFlag2 = 0
            jsonLog2["END"] = {"local_time": ""}
            jsonLogData2 = ujson.dumps(jsonLog2)
            jsonLog2.clear()
            print("CH2 Dryer Ended")
            SendStatus(2, 1)
            SendLog(2, jsonLogData2)
            ch2Cnt = 1
            ch2Led.value(0)
            ch2CurrStatus = 1

def StatusJudgment(ampsTrms, waterSensorData, lHour, cnt, m, previousMillisEnd, channelNum):
    global jsonLogFlag1, jsonLogFlag2, jsonLogFlag1C, jsonLogFlag2C
    global jsonLogFlag1F, jsonLogFlag2F, jsonLogFlag1W, jsonLogFlag2W
    global jsonLogCnt1, jsonLogCnt2, jsonLogMillis1, jsonLogMillis2
    global ch1Cnt, ch2Cnt, ch1CurrStatus, ch2CurrStatus, m1, m2
    global timeSendFlag1, timeSendFlag2
    sePrevMillis1 = 0
    sePrevMillis2 = 0
    seCnt1 = 0
    seCnt2 = 0

    if channelNum == 1 and (ampsTrms > ch1CurrW or waterSensorData or lHour > ch1FlowW) and seCnt1 == 0:
        seCnt1 = 1
        sePrevMillis1 = utime.ticks_ms()
    elif channelNum == 1 and (ampsTrms < ch1CurrW and not waterSensorData and lHour < ch1FlowW) and seCnt1 == 1:
        seCnt1 = 0

    if channelNum == 2 and (ampsTrms > ch2CurrW or waterSensorData or lHour > ch2FlowW) and seCnt2 == 0:
        seCnt2 = 1
        sePrevMillis2 = utime.ticks_ms()
    elif channelNum == 2 and (ampsTrms < ch2CurrW and not waterSensorData and lHour < ch2FlowW) and seCnt2 == 1:
        seCnt2 = 0

    if channelNum == 1 and jsonLogFlag1:
        if ampsTrms > ch1CurrW and jsonLogFlag1C == 0:
            jsonLogFlag1C = 1
            jsonLog1[str(jsonLogCnt1)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                "n": "C",
                "s": 1
            }
            if jsonLogCnt1 % 100 == 0:
                jsonLogData1 = ujson.dumps(jsonLog1)
                jsonLog1.clear()
                SendLog(1, jsonLogData1)
            jsonLogCnt1 += 1
        elif ampsTrms < ch1CurrW and jsonLogFlag1C == 1:
            jsonLogFlag1C = 0
            jsonLog1[str(jsonLogCnt1)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                "n": "C",
                "s": 0
            }
            if jsonLogCnt1 % 100 == 0:
                jsonLogData1 = ujson.dumps(jsonLog1)
                jsonLog1.clear()
                SendLog(1, jsonLogData1)
            jsonLogCnt1 += 1
        if lHour > ch1FlowW and jsonLogFlag1F == 0:
            jsonLogFlag1F = 1
            jsonLog1[str(jsonLogCnt1)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                "n": "F",
                "s": 1
            }
            if jsonLogCnt1 % 100 == 0:
                jsonLogData1 = ujson.dumps(jsonLog1)
                jsonLog1.clear()
                SendLog(1, jsonLogData1)
            jsonLogCnt1 += 1
        elif lHour < ch1FlowW and jsonLogFlag1F == 1:
            jsonLogFlag1F = 0
            jsonLog1[str(jsonLogCnt1)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                "n": "F",
                "s": 0
            }
            if jsonLogCnt1 % 100 == 0:
                jsonLogData1 = ujson.dumps(jsonLog1)
                jsonLog1.clear()
                SendLog(1, jsonLogData1)
            jsonLogCnt1 += 1
        if waterSensorData and jsonLogFlag1W == 0:
            jsonLogFlag1W = 1
            jsonLog1[str(jsonLogCnt1)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                "n": "W",
                "s": 1
            }
            if jsonLogCnt1 % 100 == 0:
                jsonLogData1 = ujson.dumps(jsonLog1)
                jsonLog1.clear()
                SendLog(1, jsonLogData1)
            jsonLogCnt1 += 1
        elif not waterSensorData and jsonLogFlag1W == 1:
            jsonLogFlag1W = 0
            jsonLog1[str(jsonLogCnt1)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis1),
                "n": "W",
                "s": 0
            }
            if jsonLogCnt1 % 100 == 0:
                jsonLogData1 = ujson.dumps(jsonLog1)
                jsonLog1.clear()
                SendLog(1, jsonLogData1)
            jsonLogCnt1 += 1

    if channelNum == 2 and jsonLogFlag2:
        if ampsTrms > ch2CurrW and jsonLogFlag2C == 0:
            jsonLogFlag2C = 1
            jsonLog2[str(jsonLogCnt2)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                "n": "C",
                "s": 1
            }
            if jsonLogCnt2 % 100 == 0:
                jsonLogData2 = ujson.dumps(jsonLog2)
                jsonLog2.clear()
                SendLog(2, jsonLogData2)
            jsonLogCnt2 += 1
        elif ampsTrms < ch2CurrW and jsonLogFlag2C == 1:
            jsonLogFlag2C = 0
            jsonLog2[str(jsonLogCnt2)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                "n": "C",
                "s": 0
            }
            if jsonLogCnt2 % 100 == 0:
                jsonLogData2 = ujson.dumps(jsonLog2)
                jsonLog2.clear()
                SendLog(2, jsonLogData2)
            jsonLogCnt2 += 1
        if lHour > ch2FlowW and jsonLogFlag2F == 0:
            jsonLogFlag2F = 1
            jsonLog2[str(jsonLogCnt2)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                "n": "F",
                "s": 1
            }
            if jsonLogCnt2 % 100 == 0:
                jsonLogData2 = ujson.dumps(jsonLog2)
                jsonLog2.clear()
                SendLog(2, jsonLogData2)
            jsonLogCnt2 += 1
        elif lHour < ch2FlowW and jsonLogFlag2F == 1:
            jsonLogFlag2F = 0
            jsonLog2[str(jsonLogCnt2)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                "n": "F",
                "s": 0
            }
            if jsonLogCnt2 % 100 == 0:
                jsonLogData2 = ujson.dumps(jsonLog2)
                jsonLog2.clear()
                SendLog(2, jsonLogData2)
            jsonLogCnt2 += 1
        if waterSensorData and jsonLogFlag2W == 0:
            jsonLogFlag2W = 1
            jsonLog2[str(jsonLogCnt2)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                "n": "W",
                "s": 1
            }
            if jsonLogCnt2 % 100 == 0:
                jsonLogData2 = ujson.dumps(jsonLog2)
                jsonLog2.clear()
                SendLog(2, jsonLogData2)
            jsonLogCnt2 += 1
        elif not waterSensorData and jsonLogFlag2W == 1:
            jsonLogFlag2W = 0
            jsonLog2[str(jsonLogCnt2)] = {
                "t": utime.ticks_diff(utime.ticks_ms(), jsonLogMillis2),
                "n": "W",
                "s": 0
            }
            if jsonLogCnt2 % 100 == 0:
                jsonLogData2 = ujson.dumps(jsonLog2)
                jsonLog2.clear()
                SendLog(2, jsonLogData2)
            jsonLogCnt2 += 1

    if channelNum == 1 and utime.ticks_diff(utime.ticks_ms(), sePrevMillis1) >= 500 and seCnt1 == 1:
        if cnt == 1:
            timeSendFlag1 = 1
            jsonLogFlag1 = 1
            jsonLogCnt1 = 1
            jsonLogMillis1 = utime.ticks_ms()
            jsonLog1["START"] = {"local_time": ""}
            seCnt1 = 0
            ch1Cnt = 0
            ch1Led.value(1)
            ch1CurrStatus = 0
            print(f"CH{channelNum} Washer Started")
            SendStatus(channelNum, 0)
        m1 = 1
    elif channelNum == 2 and utime.ticks_diff(utime.ticks_ms(), sePrevMillis2) >= 500 and seCnt2 == 1:
        if cnt == 1:
            timeSendFlag2 = 1
            jsonLogFlag2 = 1
            jsonLogCnt2 = 1
            jsonLogMillis2 = utime.ticks_ms()
            jsonLog2["START"] = {"local_time": ""}
            seCnt2 = 0
            ch2Cnt = 0
            ch2Led.value(1)
            ch2CurrStatus = 0
            print(f"CH{channelNum} Washer Started")
            SendStatus(channelNum, 0)
        m2 = 1
    else:
        if previousMillisEnd > utime.ticks_ms():
            previousMillisEnd = utime.ticks_ms()
        if m:
            if channelNum == 1:
                globals()["previousMillisEnd1"] = utime.ticks_ms()
                m1 = 0
            if channelNum == 2:
                globals()["previousMillisEnd2"] = utime.ticks_ms()
                m2 = 0
        elif cnt:
            pass
        elif channelNum == 1 and utime.ticks_diff(utime.ticks_ms(), previousMillisEnd) >= ch1EndDelayW:
            timeSendFlag1 = 1
            jsonLogFlag1C = 0
            jsonLogFlag1F = 0
            jsonLogFlag1W = 0
            jsonLogFlag1 = 0
            jsonLog1["END"] = {"local_time": ""}
            jsonLogData1 = ujson.dumps(jsonLog1)
            jsonLog1.clear()
            print("CH1 Washer Ended")
            SendStatus(1, 1)
            SendLog(1, jsonLogData1)
            ch1Cnt = 1
            ch1Led.value(0)
            ch1CurrStatus = 1
        elif channelNum == 2 and utime.ticks_diff(utime.ticks_ms(), previousMillisEnd) >= ch2EndDelayW:
            timeSendFlag2 = 1
            jsonLogFlag2C = 0
            jsonLogFlag2F = 0
            jsonLogFlag2W = 0
            jsonLogFlag2 = 0
            jsonLog2["END"] = {"local_time": ""}
            jsonLogData2 = ujson.dumps(jsonLog2)
            jsonLog2.clear()
            print("CH2 Washer Ended")
            SendStatus(2, 1)
            SendLog(2, jsonLogData2)
            ch2Cnt = 1
            ch2Led.value(0)
            ch2CurrStatus = 1

def SetDefaultVal():
    global apSsid, apPasswd, serialNo, authId, authPasswd
    global ch1DeviceNo, ch2DeviceNo, ch1CurrW, ch2CurrW
    global ch1FlowW, ch2FlowW, ch1CurrD, ch2CurrD
    global ch1EndDelayW, ch2EndDelayW, ch1EndDelayD, ch2EndDelayD
    global isCh1Live, isCh2Live, roomNo, deviceName

    apSsid = NvsGetString("apSsid", "")
    apPasswd = NvsGetString("apPasswd", "")
    serialNo = NvsGetString("serialNo", "0")
    authId = NvsGetString("authId", "")
    authPasswd = NvsGetString("authPasswd", "")
    ch1DeviceNo = NvsGetString("ch1DeviceNo", "1")
    ch2DeviceNo = NvsGetString("ch2DeviceNo", "2")
    ch1CurrW = NvsGetFloat("ch1CurrW", 0.2)
    ch2CurrW = NvsGetFloat("ch2CurrW", 0.2)
    ch1FlowW = NvsGetUint("ch1FlowW", 50)
    ch2FlowW = NvsGetUint("ch2FlowW", 50)
    ch1CurrD = NvsGetFloat("ch1CurrD", 0.5)
    ch2CurrD = NvsGetFloat("ch2CurrD", 0.5)
    ch1EndDelayW = NvsGetUint("ch1EndDelayW", 10) * 10000
    ch2EndDelayW = NvsGetUint("ch2EndDelayW", 10) * 10000
    ch1EndDelayD = NvsGetUint("ch1EndDelayD", 10) * 1000
    ch2EndDelayD = NvsGetUint("ch2EndDelayD", 10) * 1000
    isCh1Live = NvsGetBool("isCh1Live", True)
    isCh2Live = NvsGetBool("isCh2Live", True)
    roomNo = NvsGetString("roomNo", "0")
    deviceName = defaultDeviceName + serialNo
    print(f"My Name Is: {deviceName}")
    print(f"CH1: {ch1DeviceNo} CH2: {ch2DeviceNo}")
    if authId == "" or authPasswd == "":
        print("NO AUTH CODE!!! YOU NEED TO CONFIG SERVER AUTHENTICATION BY AT+SET_AUTH_ID AND AT+SET_AUTH_PASSWD IN DEBUG MODE!!!")
    if apSsid == "":
        print("NO WIFI SSID!!! YOU NEED TO CONFIG WIFI BY AT+SETAP_SSID AND AT+SETAP_PASSWD IN DEBUG MODE!!!")
    print(f"ch1CurrWash: {ch1CurrW} ch2CurrWash: {ch2CurrW}")
    print(f"ch1FlowWash: {ch1FlowW} ch2FlowWash: {ch2FlowW}")
    print(f"ch1DelayWash: {ch1EndDelayW} ch2DelayWash: {ch2EndDelayW}")
    print(f"ch1CurrDry: {ch1CurrD} ch2CurrDry: {ch2CurrD}")
    print(f"ch1DelayDry: {ch1EndDelayD} ch2DelayDry: {ch2EndDelayD}")
    print(f"ch1Enable: {isCh1Live} ch2Enable: {isCh2Live}")

def NetworkInfo():
    print(f"Name = {deviceName}")
    print(f"WiFi Status: {'Connected' if staIf.isconnected() else 'Disconnected'}")
    if staIf.isconnected():
        print(f"RSSI = {staIf.status('rssi')}")
        print(f"Local IP = {staIf.ifconfig()[0]}")
    print(f"MAC = {ubinascii.hexlify(staIf.config('mac')).decode()}")
    print(f"SSID = {apSsid}")
    print(f"PASSWORD = {apPasswd}")

async def MainLoop():
    global currMillis, previousMillis, ledMillisPrev, isWifiFail
    global ampsTrms1, ampsTrms2, waterSensorData1, waterSensorData2
    global lHour1, lHour2, flowFrequency1, flowFrequency2
    global jsonLogFlag1, jsonLogFlag2

    SetDefaultVal()
    isModeDebug = not debugPin.value()
    isCh1Mode = not ch1Mode.value()
    isCh2Mode = not ch2Mode.value()
    print(f"FW_VER: {buildDate}")
    if isModeDebug:
        print("YOU ARE IN THE DEBUG MODE!!!")
    print(f"ch1Mode: {isCh1Mode}")
    print(f"ch2Mode: {isCh2Mode}")

    # Sensor stabilization
    for _ in range(30):
        CalcIrms(ct1, 30.7)
        CalcIrms(ct2, 30.7)
        await asyncio.sleep_ms(10)

    print(f"Boot Heap: {gc.mem_free()}")
    statusPin.value(1)

    if apSsid:
        print(f"Connecting to WiFi .. {apSsid}")
        staIf.connect(apSsid, apPasswd)
        wifiTimeout = 0
        while not staIf.isconnected() and wifiTimeout < 25:
            statusPin.value(0)
            await asyncio.sleep_ms(100)
            statusPin.value(1)
            await asyncio.sleep_ms(100)
            wifiTimeout += 1
        if not staIf.isconnected():
            print("Skip WiFi Connection Due to Timeout")
        else:
            print(f"WiFi connected {staIf.ifconfig()[0]}")
            await WebsocketConnect()
            asyncio.create_task(WebServer())

    while True:
        currMillis = utime.ticks_ms()
        if isRebooting:
            await asyncio.sleep_ms(100)
            machine.reset()

        if staIf.isconnected():
            isWifiFail = 0
            statusPin.value(1)
            asyncio.create_task(WebsocketLoop())
        else:
            isWifiFail = 1
            if utime.ticks_diff(currMillis, ledMillisPrev) >= 100:
                ledMillisPrev = currMillis
                statusPin.value(not statusPin.value())

        if isModeDebug:
            ampsTrms1 = CalcIrms(ct1, 30.7)
            ampsTrms2 = CalcIrms(ct2, 30.7)

            if utime.ticks_diff(currMillis, previousMillis) >= sensPeriod:
                previousMillis = currMillis
                waterSensorData1 = drain1.value()
                waterSensorData2 = drain2.value()
                lHour1 = (flowFrequency1 * 60 / 7.5)
                lHour2 = (flowFrequency2 * 60 / 7.5)
                flowFrequency1 = 0
                flowFrequency2 = 0

            if isCh1Mode:
                StatusJudgment(ampsTrms1, waterSensorData1, lHour1, ch1Cnt, m1, previousMillisEnd1, 1)
            else:
                DryerStatusJudgment(ampsTrms1, ch1Cnt, m1, previousMillisEnd1, 1)

            if isCh2Mode:
                StatusJudgment(ampsTrms2, waterSensorData2, lHour2, ch2Cnt, m2, previousMillisEnd2, 2)
            else:
                DryerStatusJudgment(ampsTrms2, ch2Cnt, m2, previousMillisEnd2, 2)
        else:
            if utime.ticks_diff(currMillis, ledMillisPrev) >= 100:
                ledMillisPrev = currMillis
                ledStatus = 1 - ledStatus
                ch1Led.value(ledStatus)
                ch2Led.value(not ledStatus)

        await asyncio.sleep_ms(10)

# Run the main loop
try:
    asyncio.run(MainLoop())
except KeyboardInterrupt:
    print("Program interrupted")
finally:
    asyncio.new_event_loop()