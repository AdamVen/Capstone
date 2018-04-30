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


class ParameterGraph(tk.Frame):

    def __init__(self, xStart, xEnd, yStart, yEnd, title, lowerRange, upperRange):
        tk.Frame.__init__(self)
        label = tk.Label(self, text=title, font=("Courier", 55))
        label.pack(pady=10, padx=10)

        tk.Frame.pack(self)

        self.xData = []
        self.yData = []

        self.index = 0

        self.f = Figure(figsize = (2.5, 1.5), dpi = 100)
        self.a = self.f.add_subplot(111)
        self.a.plot(self.xData, self.yData)
        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tk.Frame.pack(self)
        print("initialized")

    def addValue(self, y):
        self.xData.append(self.index)
        self.yData.append(y)

        self.index = self.index + 1

        if len(self.xData) > 10:
            self.xData.pop(0)
            self.yData.pop(0)

        self.drawGraph()

    def drawGraph(self):
        self.a.clear()
        self.a.plot(self.xData, self.yData)
        self.canvas.draw()
        tk.Frame.pack(self)
        print(self.xData[-1])

