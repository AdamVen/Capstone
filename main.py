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
#from GUIThread import GUIThread

# Google Project Api Imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Multi-threading imports
import threading

# Read USB data
import serial
import time

# Time stamping
import datetime

# GUI
#import tkinter as tk
from tkinter import ttk
from tkinter import *

# Graphing
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation

# For speed improvements
from collections import deque

def animate(i):
    lineCurGood.set_data(range(len(curDataGood)), curDataGood)
    lineCurBad.set_data(range(len(curDataGood)), curDataBad)
    lineDistGood.set_data(range(len(curDataGood)), distDataGood)
    lineDistBad.set_data(range(len(curDataGood)), distDataBad)
    lineAngGood.set_data(range(len(curDataGood)), angDataGood)
    lineAngBad.set_data(range(len(curDataGood)), angDataBad)
    lineAccGood.set_data(range(len(curDataGood)), accDataGood)
    lineAccBad.set_data(range(len(curDataGood)), accDataBad)
    return lineCurGood, lineCurBad, lineDistGood, lineDistBad,\
           lineAngGood, lineAngBad, lineAccGood, lineAccBad

def animateinit():
    return lineCurGood, lineCurBad, lineDistGood, lineDistBad,\
           lineAngGood, lineAngBad, lineAccGood, lineAccBad

def putData(data, param):
    if param == 0:
        if curRange[0] < data < curRange[1]:
            curDataGood.append(data)
            curDataBad.append(None)
        else:
            curDataGood.append(None)
            curDataBad.append(data)

        curDataGood.popleft()
        curDataBad.popleft()

    elif param == 1:
        if distRange[0] < data < distRange[1]:
            distDataGood.append(data)
            distDataBad.append(None)
        else:
            distDataGood.append(None)
            distDataBad.append(data)

        distDataGood.popleft()
        distDataBad.popleft()
        print(distDataGood)

    elif param == 2:
        if angRange[0] < data < angRange[1]:
            angDataGood.append(data)
            angDataBad.append(None)
        else:
            angDataGood.append(None)
            angDataBad.append(data)
        angDataGood.popleft()
        angDataBad.popleft()

    elif param == 3:
        if accRange[0] < data < accRange[1]:
            accDataGood.append(data)
            accDataBad.append(None)
        else:
            accDataGood.append(None)
            accDataBad.append(data)
        accDataGood.popleft()
        accDataBad.popleft()

def updateFrame():
    LABEL.config(font=("Courier", 55))
    LABEL.pack()
    f.pack()
    ROOT.update()

# Define x limit
xLim = 50

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

# Set-up USB
ser = serial.Serial('/dev/ttyUSB0', BAUD_RATE)

# Load data from excel sheet
for r in range(CONST_START_ROW, CONST_END_ROW + 1):
    for angPlot in range(CONST_START_COLUMN, CONST_END_COLUMN + 1):
        cellStr = ws.cell(row = r, column = angPlot)
        weldingParameters[r - CONST_START_ROW][angPlot - CONST_START_COLUMN] = cellStr.value

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

# Data plotting variables
curDataGood = deque([None] * xLim, maxlen = xLim)
distDataGood = deque([None] * xLim, maxlen = xLim)
angDataGood = deque([None] * xLim, maxlen = xLim)
accDataGood = deque([None] * xLim, maxlen = xLim)

curDataBad = deque([None] * xLim, maxlen = xLim)
distDataBad = deque([None] * xLim, maxlen = xLim)
angDataBad = deque([None] * xLim, maxlen = xLim)
accDataBad = deque([None] * xLim, maxlen = xLim)

curRange = [198, 202]
distRange = [10, 12]
angRange = [85, 95]
accRange = [-0.2, 0.2]

# GUI Set-Up
outStr = ""
ROOT = Tk()
f = Frame(ROOT)
ROOT.attributes("-fullscreen", True)
displayMode = 2
var = StringVar()
var.set("test")
LABEL = Label(f, textvariable = var)

fig = Figure(figsize = (12, 7), dpi = 100)

curPlot = fig.add_subplot(221)
distPlot = fig.add_subplot(222)
angPlot = fig.add_subplot(223)
accPlot = fig.add_subplot(224)

curPlot.set_xlim([0, xLim])
distPlot.set_xlim([0, xLim])
angPlot.set_xlim([0, xLim])
accPlot.set_xlim([0, xLim])

curPlot.set_ylim(curRange)
distPlot.set_ylim(distRange)
angPlot.set_ylim(angRange)
accPlot.set_ylim(accRange)
#curPlot.plot(curDataGood, 'k', linewidth = 3)
lineCurGood, = curPlot.plot([0], [0], color = 'black')
lineCurBad, = curPlot.plot([0], [0],color = 'red')
lineDistGood, = distPlot.plot([0], [0],color = 'black')
lineDistBad, = distPlot.plot([0], [0],color = 'red')
lineAngGood, = angPlot.plot([0], [0],color = 'black')
lineAngBad, = angPlot.plot([0], [0],color = 'red')
lineAccGood, = accPlot.plot([0], [0],color = 'black')
lineAccBad, = accPlot.plot([0], [0],color = 'red')

curPlot.axis('off')
curPlot.set_title("Current")
distPlot.axis('off')
distPlot.set_title("Distance")
angPlot.axis('off')
angPlot.set_title("Angle")
accPlot.axis('off')
accPlot.set_title("Acceleration")

canvas = FigureCanvasTkAgg(fig, master=ROOT)
canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=True)

Frame.pack(f)

ani = animation.FuncAnimation(fig, animate, interval=40, init_func = animateinit, blit = True)
ROOT.config(cursor="none")
print('entering main loop')
ROOT.mainloop()

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

        #LOOP_ACTIVE = True


        prevTime = time.time()


        while time.time() < timeout:
            data = str(ser.readline())

            try:
                rawData, measurement = data.split(":")
                measurementValue = measurement.split("\\", 1)[0]
            except:
                rawData = ""
                print('Serial Read Error')

            if "C" in rawData:
                param = 0
                measurementValue = 200 + random.uniform(-3, 3)
                current.append(round(float(measurementValue), 3))

            elif "D" in rawData:
                param = 1
                measurementValue = 11 + random.uniform(-2, 2)
                distance.append(measurementValue)

            elif "angLR" in rawData:
                angle.append(measurementValue)
                param = 2
                if float(angle[-1]) > 75:
                    i = 0
                elif float(angle[-1]) < 55:
                    i = 2
                else:
                    i = 1

            elif "accLR" in rawData:
                accLR.append(round(float(measurementValue), 3))
                param = 3

            elif "accFB" in rawData:
                accFB.append(round(float(measurementValue), 3))
                param = 4

            elif "angFB" in rawData:
                param = 4

            parsedData = measurementValue

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
            elif displayMode == 2:
                #newGUIThread = threading.Thread(target=GUIThread, args=(parsedData, param, paramGraph))
                #newGUIThread.start()
                print(str(time.time() - prevTime))
                prevTime = time.time()
                putData(float(parsedData), param)
                #paramGraph.drawGraph()
                #f.pack()
                ROOT.update()
                ROOT.update_idletasks()

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