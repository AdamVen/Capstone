# The purpose of this program is to stream video with a dynamic text overlay simulating welding parameters
# that will later be obtained from an instrumentation module.

# RPi peripherals imports
import picamera

# Time/Sleep imports
from time import sleep
import datetime as dt

# Networking imports
import socket
import subprocess

# Excel imports
import openpyxl

# GUI imports
from tkinter import *

# Enum import to facilitate looping through welding parameters
from enum import Enum

# Google Project Api Imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Multithreading imports
import threading
from threading import Timer

# Read USB data
import serial
import time

# For time stamping data
import datetime

# For writing video
import io

# Create client to interact with Google Drive Api
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('/home/pi/Downloads/client.json', scope)
client = gspread.authorize(creds)

# Find workbook and open first sheet
sheet = client.open("WeldingReadIn").sheet1

# Open up welding parameter data worksheet
wb = openpyxl.load_workbook('/home/pi/Downloads/WeldingParameters.xlsx')
ws = wb["MIG"]

# Constants
CONST_START_ROW = 5
CONST_END_ROW = 48
CONST_START_COLUMN = 4
CONST_END_COLUMN = 15
UPDATE_FREQ = 50
BAUD_RATE = 57600
SESSION_LENGTH = 60 # In seconds

# Create 2D Array to hold parameter data
w = CONST_END_ROW - CONST_START_ROW + 1
h = CONST_END_ROW - CONST_START_ROW + 1
weldingParameters = [['-1' for x in range(w)] for y in range(h)] # weldingParameters[r][c]

# Welding Parameters
distance = [0]
current = [0]
angle = [0]
acceleration = [['-1' for x in range(3)] for y in range(2)] # [X1 Y1 Z1; X2 Y2 Z2]
accFB = [0]
accLR = [0]
currentDispV =  0
timestamp = []
parameterList = []
parameterList.extend((angle, distance, accFB, accLR, current, timestamp))

# Parameter defines for Table Look-up
metal = ['0', '1']
transfer = ['0', '1']
thickness = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
metalIndex = int(sheet.cell(3, 3).value)
transferIndex = int(sheet.cell(4, 3).value)
thicknessIndex = int(sheet.cell(5, 3).value)

# For iterating through Google Sheets cells
cellIndex = 0
index = 0
indexOffset = 0

# For Google Sheets threads
lock = threading.Lock()

# Create ID
id = metal[metalIndex] + transfer[transferIndex] + thickness[thicknessIndex]

# Set-up USB
ser = serial.Serial('/dev/ttyUSB0', BAUD_RATE)

# Load data from excel sheet
for r in range(CONST_START_ROW, CONST_END_ROW + 1):
    for c in range(CONST_START_COLUMN, CONST_END_COLUMN + 1):
        cellStr = ws.cell(row = r, column = c)
        weldingParameters[r - CONST_START_ROW][c - CONST_START_COLUMN] = cellStr.value

# Extract ID Column
idCol = [item[11] for item in weldingParameters]

# Create ID
id = metal[metalIndex] + transfer[transferIndex] + thickness[thicknessIndex]

# Get table index from id
tableIndex = idCol.index(id)

# Load welding parameter information from table
currentLow = weldingParameters[tableIndex][3]
currentHigh = weldingParameters[tableIndex][4]
shieldingGas = weldingParameters[tableIndex][5]
voltageRange = weldingParameters[tableIndex][6]
thinWireSize = weldingParameters[tableIndex][7]
thinWFS = weldingParameters[tableIndex][8]
thickWireSize = weldingParameters[tableIndex][9]
thickWFS = weldingParameters[tableIndex][10]

# Additional welding parameter information
distLow = 6.35
distHigh = 12.7
angleLow = [75, 40, 60]
angleHigh = [105, 50, 70]
angleType = ['Butt Weld', 'T-Joint', 'Lap Joint']

# GUI Set-Up
outStr = ""
ROOT = Tk()
f = Frame(ROOT)
ROOT.attributes("-fullscreen", True)


class dualOutput(object):
    def __init__(self, filename, con):
        self.output_file = io.open(filename, 'wb')
        self.output_sock = con

    def write(self, buf):
        self.output_file.write(buf)
        self.output_sock.write(buf)

    def flush(self):
        self.output_file.flush()
        self.output_sock.flush()

    def close(self):
        self.output_file.close()
        self.output_sock.close()

def SheetsThread(indexOffset):
    with lock:
        for paramIndex in range(0, 6):
            # Select Range
            cell_list = sheet.range(indexOffset + 3, paramIndex + 5, indexOffset + UPDATE_FREQ + 3, paramIndex + 5)

            cellIndex = 0

            for cell in cell_list:
                cell.value = parameterList[paramIndex][cellIndex]
                cellIndex = cellIndex + 1

            sheet.update_cells(cell_list)

            del parameterList[paramIndex][0:UPDATE_FREQ]

f = Frame(ROOT)
var = StringVar()
var.set("test")
LABEL = Label(f, textvariable = var)

def updateFrame():
    LABEL.config(font=("Courier", 55))
    LABEL.pack()
    f.pack()
    ROOT.update()

with picamera.PiCamera() as camera:
    camera.resolution = (1920, 1080)
    camera.framerate = 30
    camera.brightness = 55
    camera.annotate_text_size = 16
    i = 0

    currentTime = time.time()

    streamFlag = int(sheet.cell(6, 3).value)

    try:
        tsString = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

        if ((streamFlag == 1) or (streamFlag == 3)):
            server_socket = socket.socket()

            try:
                server_socket.bind(('0.0.0.0', 8000))
                print('Waiting on connection via port 8000')
            except:
                server_socket.bind(('0.0.0.0', 8001))
                print('Waiting on connection via port 8001')

            server_socket.listen(0)
            connection = server_socket.accept()[0].makefile('wb')

            if (streamFlag == 1):
                print('Stream Starting')
                camera.start_recording(connection, format='h264')
            else:
                print('Stream and Recording Starting')
                customOutput = dualOutput('/home/pi/Downloads/' + tsString + '.h264', connection)
                camera.start_recording(customOutput, format='h264')

        elif (streamFlag == 2):
            print('Recording Starting')
            camera.start_recording('/home/pi/Downloads/' + tsString + '.h264')

        timeout = time.time() + SESSION_LENGTH

        LOOP_ACTIVE = True
        ROOT.config(cursor="none")

        while time.time() < timeout:

            data = str(ser.readline())

            try:
                param, measurement = data.split(":")
                measurementValue = measurement.split("\\", 1)[0]
            except:
                param = ""
                print('Serial Read Error')

            if "angLR" in param:
                angle.append(measurementValue)

                if float(angle[-1]) > 75:
                    i = 0
                elif float(angle[-1]) < 55:
                    i = 2
                else:
                    i = 1
            else:
                angle.append(angle[-1])

            if "D" in param:
                distance.append(measurementValue)
            else:
                distance.append(distance[-1])

            if "LR" in param:
                accLR.append(round(float(measurementValue), 3))
            else:
                accLR.append(accLR[-1])

            if "FB" in param:
                accFB.append(round(float(measurementValue), 3))
            else:
                accFB.append(accFB[-1])

            if "C" in param:
                current.append(round(float(measurementValue), 3))
            else:
                current.append(current[-1])

            index = index + 1
            timestamp.append(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

            currentStr = 'Current: ' + str(currentLow) + ' < ' + str(current[-1])[:3] + ' < ' + str(currentHigh) + '\n'
            distanceStr = 'Distance: ' + str(distLow) + ' < ' + str(distance[-1])[:5] + ' < ' + str(distHigh) + '\n'
            angleStr = 'Angle (' + str(angleType[i]) + '): ' + str(angleLow[i]) + ' < ' + str(angle[-1])[:3] + ' < ' + str(angleHigh[i]) + '\n'
            accStr = 'LR Acc: ' + str(accLR[-1])[:3] + ' FB Acc: ' + str(accFB[-1])[:3]
            outStr = currentStr + distanceStr + angleStr + accStr
            camera.annotate_text = outStr

            var.set(outStr)
            updateFrame()

            # Call thread to write to Google sheets and update GUI every UPDATE_FREQ samples
            if (index % UPDATE_FREQ == 0):
                newSheetThread = threading.Thread(target = SheetsThread, args = (indexOffset, ))
                newSheetThread.start()
                indexOffset = index

        camera.stop_recording()

    finally:
        if(streamFlag == 1 or streamFlag == 3):
            connection.close()
            server_socket.close()
            print('Stream Ended')
        else:
            print('Recording Complete')

    f.destroy()
    ROOT.destroy()