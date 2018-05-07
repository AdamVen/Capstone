# Author: Adam Vengroff
# Description: This class creates a thread to generate a sine wave with a frequency
#              proportional to the difference between the ideal value and measured

# Audio imports
import os

def SoundThread(idealRange, measurementValue):
    if not idealRange[0] < int(measurementValue) < idealRange[1]:
        idealValue = (idealRange[0] + idealRange[1]) / 2
        freq = (((idealValue - int(measurementValue)) / idealValue) + 1) * 1000

        if freq < 200:
            freq = 200

        os.system('play --no-show-progress -n synth %s sin %s' % (0.4, freq))