# Author: Adam Vengroff
# Description: This class allows for a graph to be made and updated in real-time

# For embedding graphs into GUI
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
style.use('ggplot')

# For GUI
import tkinter as tk
from tkinter import ttk
from tkinter import *


class ParameterGraph(tk.Frame):

    def __init__(self, xStart, xEnd, yStart, yEnd, title, lowerRange, upperRange):
        tk.Frame.__init__(self)
        #label = tk.Label(self, text=title, font=("Courier", 55))
        #label.pack(pady=1, padx=1)

        self.curData = []
        self.distData = []
        self.angData = []
        self.accData = []

        self.f = Figure(figsize = (12, 7), dpi = 100)

        self.a = self.f.add_subplot(221)
        self.a.plot([])
        self.a.axis('off')
        self.a.set_title("Current")

        self.b = self.f.add_subplot(222)
        self.b.plot([])
        self.b.axis('off')
        self.b.set_title("Distance")

        self.c = self.f.add_subplot(223)
        self.c.plot([])
        self.c.axis('off')
        self.c.set_title("Angle")

        self.d = self.f.add_subplot(224)
        self.d.plot([])
        self.d.axis('off')
        self.d.set_title("Acceleration")

        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tk.Frame.pack(self)
        print("initialized")

    def addValue(self, data, param):
        if param == 0:
            self.curData.append(data)
            dataArray = self.curData
        elif param == 1:
            self.distData.append(data)
            dataArray = self.distData
        elif param == 2:
            self.angData.append(data)
            dataArray = self.angData
        else:
            dataArray = self.accData

        self.checkSize(dataArray)
        self.drawGraph(param, dataArray)

    def checkSize(self, dataArray):
        if len(dataArray) > 10:
            dataArray.pop(0)

    def drawGraph(self, param, dataArray):

        if param == 0:
            subplot = self.a
            title = "Current"
        if param == 1:
            subplot = self.b
            title = "Distance"
        if param == 2:
            subplot = self.c
            title = "Angle"
        if param == 3:
            subplot = self.d
            title = "Acceleration"

        subplot.clear()
        subplot.plot(dataArray)
        subplot.axis('off')
        subplot.set_title(title)
        self.canvas.draw()
        tk.Frame.pack(self)
