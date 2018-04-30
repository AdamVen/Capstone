# Author: Adam Vengroff
# Description: This class allows data to be written to a Google Sheet

# Multi-threading imports
import threading

# For Google Sheets threads
lock = threading.Lock()

def SheetsThread(indexOffset, UPDATE_FREQ, parameterList, sheet):
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