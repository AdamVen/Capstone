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

# Define x limit
xLim = 50


class ParameterGraph(tk.Frame):

    def __init__(self, curRange, distRange, angRange, accRange):
        tk.Frame.__init__(self)

        self.curDataGood = [None] * xLim
        self.distDataGood = [None]  * xLim
        self.angDataGood = [None]  * xLim
        self.accDataGood = [None]  * xLim

        self.curDataBad = [None]  * xLim
        self.distDataBad = [None]  * xLim
        self.angDataBad = [None]  * xLim
        self.accDataBad = [None]  * xLim

        self.curRange = curRange
        self.distRange = distRange
        self.angRange = angRange
        self.accRange = accRange

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

    def putData(self, data, param):
        if param == 0:
            if self.curRange[0] < data < self.curRange[1]:
                self.curDataGood.append(data)
                self.curDataBad.append(None)
            else:
                self.curDataGood.append(None)
                self.curDataBad.append(data)

            self.curDataGood.pop(0)
            self.curDataBad.pop(0)

        elif param == 1:
            if self.distRange[0] < data < self.distRange[1]:
                self.distDataGood.append(data)
                self.distDataBad.append(None)
            else:
                self.distDataGood.append(None)
                self.distDataBad.append(data)

            self.distDataGood.pop(0)
            self.distDataBad.pop(0)


        elif param == 2:
            if self.angRange[0] < data < self.angRange[1]:
                self.angDataGood.append(data)
                self.angDataBad.append(None)
            else:
                self.angDataGood.append(None)
                self.angDataBad.append(data)
            self.angDataGood.pop(0)
            self.angDataBad.pop(0)
            print(self.angDataGood)
            print(self.angDataBad)
        else:
            if self.accRange[0] < data < self.accRange[1]:
                self.accDataGood.append(data)
                self.accDataBad.append(None)
            else:
                self.accDataGood.append(None)
                self.accDataBad.append(data)
            self.accDataGood.pop(0)
            self.accDataBad.pop(0)

        self.updateGraph(param)

    def updateGraph(self, param):
        if param == 0:
            subplot = self.a
            subplot.clear()
            subplot.plot(self.curDataGood, 'k', linewidth = 3)
            subplot.plot(self.curDataBad, 'r', linewidth = 3.2)
            subplot.axis('off')
            subplot.set_title("Current")
        elif param == 1:
            subplot = self.b
            subplot.clear()
            subplot.plot(self.distDataGood, 'k', linewidth = 3)
            subplot.plot(self.distDataBad, 'r', linewidth = 3.2)
            subplot.axis('off')
            subplot.set_title("Distance")
        elif param == 2:
            subplot = self.c
            subplot.clear()
            subplot.plot(self.angDataGood, 'k', linewidth = 3)
            subplot.plot(self.angDataBad, 'r', linewidth = 3.2)
            subplot.axis('off')
            subplot.set_title("Angle")
        else:
            subplot = self.d
            subplot.clear()
            subplot.plot(self.accDataGood, 'k', linewidth = 3)
            subplot.plot(self.accDataBad, 'r', linewidth = 3.2)
            subplot.axis('off')
            subplot.set_title("Acceleration")

    def drawGraph(self):
        try:
            self.canvas.draw()
            tk.Frame.pack(self)
        except:
            print("Graph Render Error")
