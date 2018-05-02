# Author: Adam Vengroff
# Description: This class allows data to be written to a Google Sheet

# Multi-threading imports
import threading

# For coordinating threads
lockGUI = threading.Lock()

def GUIThread(data, param, paramGraph):
    with lockGUI:
        paramGraph.putData(float(data), param)