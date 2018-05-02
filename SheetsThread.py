# Author: Adam Vengroff
# Description: This class creates a thread to write data to Google Sheets

# Multi-threading imports
import threading

# For coordinating threads
lockThread = threading.Lock()

def SheetsThread(indexOffset, UPDATE_FREQ, parameterList, sheet):
    with lockThread:
        for paramIndex in range(0, 6):
            # Select Range
            cell_list = sheet.range(indexOffset + 3, paramIndex + 5, indexOffset + UPDATE_FREQ + 3, paramIndex + 5)

            cellIndex = 0

            for cell in cell_list:
                cell.value = parameterList[paramIndex][cellIndex]
                cellIndex = cellIndex + 1

            sheet.update_cells(cell_list)

            del parameterList[paramIndex][0:UPDATE_FREQ]