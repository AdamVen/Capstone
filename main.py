# Author: Adam Vengroff
# Description: This software processes serial data

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

# Custom-written module imports
from DualOutput import DualOutput
from ParameterGraph import ParameterGraph
from SheetsThread import SheetsThread
from GUIThread import GUIThread

# Google Project Api Imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Multi-threading imports
import threading

# Read USB data
import serial
import time

# For time stamping data
import datetime

# For writing video
import io

# For GUI
import tkinter as tk
from tkinter import ttk
from tkinter import *

# For embedding graphs into GUI
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

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
SESSION_LENGTH = 90 # In seconds

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
angleFrame = Frame(ROOT)
ROOT.attributes("-fullscreen", True)
displayMode = 2

f = Frame(ROOT)
var = StringVar()
var.set("test")
LABEL = Label(f, textvariable = var)

# Instantiate graph glasses
paramGraph = ParameterGraph([198, 202], [10, 12], [85, 95], [-0.2, 0.2])
ROOT.update()
import random

#while (1):
#    x = 200 + (3 * math.sin(index))
#    paramGraph.addValue(x, 0)
#    print(x)
#    index = index + 0.01
#    if index > 6.28:
#        index = 0
#    ROOT.update()


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
    param = 0

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
                customOutput = DualOutput('/home/pi/Downloads/' + tsString + '.h264', connection)
                camera.start_recording(customOutput, format='h264')

        elif (streamFlag == 2):
            print('Recording Starting')
            camera.start_recording('/home/pi/Downloads/' + tsString + '.h264')

        timeout = time.time() + SESSION_LENGTH

        LOOP_ACTIVE = True
        ROOT.config(cursor="none")

        prevTime = time.time()

        while time.time() < timeout:
            data = str(ser.readline())

            try:
                rawData, measurement = data.split(":")
                measurementValue = measurement.split("\\", 1)[0]
            except:
                rawData = ""
                print('Serial Read Error')

            if "angLR" in rawData:
                angle.append(measurementValue)
                param = 2
                if float(angle[-1]) > 75:
                    i = 0
                elif float(angle[-1]) < 55:
                    i = 2
                else:
                    i = 1
            else:
                angle.append(angle[-1])

            if "D" in rawData:
                param = 1
                measurementValue = 11 + random.uniform(-2, 2)
                distance.append(measurementValue)
            else:
                distance.append(distance[-1])

            if "accLR" in rawData:
                accLR.append(round(float(measurementValue), 3))
                param = 3
            else:
                accLR.append(accLR[-1])

            if "accFB" in rawData:
                accFB.append(round(float(measurementValue), 3))
            else:
                accFB.append(accFB[-1])

            if "C" in rawData:
                param = 0
                measurementValue = 200 + random.uniform(-3, 3)
                current.append(round(float(measurementValue), 3))
            else:
                current.append(current[-1])

            parsedData = measurementValue
            print(str(rawData) + str(parsedData))

            index = index + 1
            timestamp.append(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

            currentStr = 'Current: ' + str(currentLow) + ' < ' + str(current[-1])[:3] + ' < ' + str(currentHigh) + '\n'
            distanceStr = 'Distance: ' + str(distLow) + ' < ' + str(distance[-1])[:5] + ' < ' + str(distHigh) + '\n'
            angleStr = 'Angle (' + str(angleType[i]) + '): ' + str(angleLow[i]) + ' < ' + str(angle[-1])[:3] + ' < ' + str(angleHigh[i]) + '\n'
            accStr = 'LR Acc: ' + str(accLR[-1])[:3] + ' FB Acc: ' + str(accFB[-1])[:3]
            outStr = currentStr + distanceStr + angleStr + accStr
            camera.annotate_text = outStr

            if displayMode == 1:
                var.set(outStr)
                updateFrame()

            if displayMode == 2:
                newGUIThread = threading.Thread(target=GUIThread, args=(parsedData, param, paramGraph))
                newGUIThread.start()
                print(str(time.time() - prevTime))
                prevTime = time.time()
                ROOT.update()
                #paramGraph.putData(float(parsedData), param)
                paramGraph.drawGraph()
            # Call thread to write to Google sheets and update GUI every UPDATE_FREQ samples
            if (index % UPDATE_FREQ == 0):
                newSheetThread = threading.Thread(target = SheetsThread, args = (indexOffset, UPDATE_FREQ, parameterList, sheet, ))
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