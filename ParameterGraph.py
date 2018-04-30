# Author: Adam Vengroff
# Description: This class allows for a graph to be made and updated in real-time

# For embedding graphs into GUI
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

# For GUI
import tkinter as tk
from tkinter import ttk


class ParameterGraph(tk.Frame):

    def __init__(self, xStart, xEnd, yStart, yEnd, title, lowerRange, upperRange):
        tk.Frame.__init__(self)
        label = tk.Label(self, text=title, font=("Courier", 55))
        label.pack(pady=10, padx=10)

        f = Figure(figsize = (5, 5), dpi = 100)
        a = f.add_subplot(111)
        a.plot([1, 2, 3, 4, 5, 6, 7, 8], [4, 5, 1, 3, 5, 6, 7, 5])

        canvas = FigureCanvasTkAgg(f, self)
        canvas.show()
        canvas.get_tk_widget().pack(side = tk.BOTTOM, fill=tk.BOTH, expand = True)
        canvas._tkcanvas.pack(side = tk.TOP, fill = tk.BOTH, expand = True)

        tk.Frame.pack(self)

