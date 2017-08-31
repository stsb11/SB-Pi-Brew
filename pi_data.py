# Sense hat data logger v0.5
from sense_hat import SenseHat
from ISStreamer.Streamer import Streamer
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import time
import os
import datetime
import glob
import subprocess

savePath = "/home/pi/mjpg-streamer/mjpg-streamer-experimental/www/"

# Set this to True if the Sense hat is plugged straight into the Pi. This will try to account for effect of the heat from the CPU when taking temperature measurements.
useHeuristicTemp = False

# Set this to True if you have a DS18B20 temperature probe on GPIO4.
DS18B20_connected = True

# create a Streamer instance (currently disabled)
# streamer = Streamer(bucket_name="YOUR_BUCKET_NAME", bucket_key="YOUR_KEY", access_key="YOUR_KEY")

# The sense hat temperatures are very inaccurate, as the heat from the CPU skews them.
# The program uses a heuristic to approximate what the actual ambient temperature is.

# Code to handle external DS18B20 temperature probe (where connected)
if DS18B20_connected == True:
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    base_dir = '/sys/bus/w1/devices/'
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'

def read_temp_raw2():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp_raw():
    catdata = subprocess.Popen(['cat',device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = catdata.communicate()
    out_decode = out.decode('utf-8')
    lines = out_decode.split('\n')
    return lines

def read_temp2():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')

    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = round(float(temp_string) / 1000.0, 1)
        temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_c #, temp_f

# THIRD PARTY CODE ENDS HERE


def getCPUtemperature():
     res = os.popen('vcgencmd measure_temp').readline()
     return(res.replace("temp=","").replace("'C\n",""))

# Function to pick up the number of lines in the sensor reading files.
def file_len(fname):
     i = -1
     with open(fname) as f:
         for i, l in enumerate(f):
             pass
     return i + 1

# Function to poll the sense hat.
# calctemp - The previous temperature reading. The sense hat often gives wildly erroneous values.
# humidity - previous humidity reading.
# pressure - previous pressure reading.
# returns a tuple containing new values.
def getSensorData(calctemp, humidity, pressure):
    oldtemp=calctemp
    oldhumid=humidity
    oldpressure=pressure
    cpuTemp=int(float(getCPUtemperature()))
    
    if useHeuristicTemp == True:
         # Use CPU temp and pressure sensor temperature to approximate temperature.
         # Got this from the web; not my idea. Can't remember where from. 
         ambient = sense.get_temperature_from_pressure()
         calctemp = round(ambient - ((cpuTemp - ambient)/ 1.5), 1)
    else:
         # Read from both temp sensors and take an average.
         calctemp = sense.get_temperature_from_pressure()
         calctemp += sense.get_temperature_from_humidity()
         calctemp = round(calctemp / 2, 1)

    humidity = round(sense.get_humidity(), 1)
    pressure = round(sense.get_pressure(), 1)

    # As alluded to above, the sensors sometimes report temperatures of -100 to +300C.
    # This serves as a basic sanity check to prevent the graphs from becoming unreadable.
    if int(calctemp) > 70 or int(calctemp) < -20:
        calctemp = oldtemp

    if int(humidity) > 110 or int(humidity) < 0:
        humidity = oldhumid
        
    if int(pressure) > 1500 or int(pressure) < 750:
        pressure = oldpressure
        
    return calctemp, humidity, pressure, cpuTemp

# Updates the data files with the most recent reading.
def updateFile(theFile, sensorReading):
    with open(theFile, "a") as out_file:
        out_file.write(str(sensorReading) + "\n")

    # Sampling once a minute, there are 1440 minutes in a day.
    # Store in a variable, as we'll use this to set xlim in the graph later.
    f_len = file_len(theFile)

    # When the file has 24 hours data, remove the oldest data point.
    if f_len > 1440:
        with open(theFile, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(theFile, 'w') as fout:
            fout.writelines(data[1:])

    # Put the data into a list for processing.
    dataFile = open(theFile).readlines()
    return dataFile
     
def plotGraph(theFile, sensorType, sensorReading):
    dataFile = updateFile(theFile, sensorReading)
    myData = list()
    
    # We'll set the y-axis scale for ourselves, based on the
    # lowest and highest readings we ever see. Use these as start points.
    lowestTemp=1500
    highestTemp=-50

    # Pass through file to find Y-axis min/max values.
    for lines in dataFile:
        nextReading = lines.replace('\n', '')
        myData.append(nextReading)

        if float(nextReading) > highestTemp:
            highestTemp = float(nextReading)

        if float(nextReading) < lowestTemp:
            lowestTemp = float(nextReading)

    # Plot the graphs
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel('Time (Past 24 hours)')
    currTime = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S')

    # Label up some stats...
    ax.text(0.015, 0.05, 'Min: ' + str(lowestTemp) + ', Max: ' + str(highestTemp),
        horizontalalignment='left',
        verticalalignment='center',
        fontsize=14, color='black',
        transform=ax.transAxes)

    # Set up graph labels and scale depending on data...
    if sensorType == "T":
        cpuTemp=round(float(getCPUtemperature()), 1)
        ax.set_title('Inside: ' + str(sensorReading) + "C, CPU: " + str(cpuTemp) + "C @ " + currTime + ".")
        ax.set_ylabel('C')
        plt.ylim(lowestTemp - 1, highestTemp + 1)
        saveName = savePath + "temp.png"
        ax.plot(myData, "r-")
    if sensorType == "T2":
        ax.set_title('Outside: ' + str(sensorReading) + "C @ " + currTime + ".")
        ax.set_ylabel('C')
        plt.ylim(lowestTemp - 1, highestTemp + 1)
        saveName = savePath + "temp2.png"
        ax.plot(myData, "r-")
    if sensorType == "T3":
        ax.set_title('CPU temperature: ' + str(sensorReading) + "C @ " + currTime + ".")
        ax.set_ylabel('C')
        plt.ylim(lowestTemp - 1, highestTemp + 1)
        saveName = savePath + "temp3.png"
        ax.plot(myData, "g-")
    elif sensorType == "H":
        ax.set_title('Relative humidity: ' + str(sensorReading) + "%rH @ " + currTime + ".")
        ax.set_ylabel('%rH')
        plt.ylim(lowestTemp - 1, highestTemp + 1)
        saveName = savePath + "humidity.png"
        ax.plot(myData)
    elif sensorType == "P":
        ax.set_title('Air pressure: ' + str(sensorReading) + "mb @ " + currTime + ".")
        ax.set_ylabel('Millibars (mb)')
        plt.ylim(lowestTemp - 4, highestTemp + 4)
        saveName = savePath + "pressure.png"
        ax.plot(myData, "k-")

    plt.xlim(0, file_len(theFile))
    # Remove 0 - 1440 values from X-axis.
    frame = plt.gca()
    frame.axes.get_xaxis().set_ticklabels([])

    # Save PNG file for use on web page.
    plt.savefig(saveName, bbox_inches='tight')
    plt.close(fig)

# Dual graph plot.
def plotDualGraph(file1, file2):
    # We'll set the y-axis scale for ourselves, based on the
    # lowest and highest readings we ever see. Use these as start points.
    lowestTemp=1500
    highestTemp=-50
    lowestInTemp=1500
    highestInTemp=-50
    lowestOutTemp=1500
    highestOutTemp=-50
    dataFile1 = open(file1).readlines()
    dataFile2 = open(file2).readlines()
    myDataT1 = []
    myDataT2 = []
    
    # Pass through file to find Y-axis min/max values for temperature...
    for lines in dataFile1:
        nextReading = lines.replace('\n', '')
        myDataT1.append(nextReading)

        if float(nextReading) > highestTemp:
            highestTemp = float(nextReading)
            highestInTemp = float(nextReading)

        if float(nextReading) < lowestTemp:
            lowestTemp = float(nextReading)
            lowestInTemp = float(nextReading)

    # And again for other data set...
    for lines in dataFile2:
        nextReading = lines.replace('\n', '')
        myDataT2.append(nextReading)

        if float(nextReading) > highestTemp:
            highestTemp = float(nextReading)
        if float(nextReading) < lowestTemp:
            lowestTemp = float(nextReading)
        if float(nextReading) > highestOutTemp:
            highestOutTemp = float(nextReading)
        if float(nextReading) < lowestOutTemp:
            lowestOutTemp = float(nextReading)
            
    # Plot the graph
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel('Time (Past 24 hours)')
    currTime = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S')
    
    # Set up graph labels and scale depending on data...
    ax.set_title('Cabinet (red): ' + str(myDataT1[len(myDataT1)-1]) + "C, Garage (blue): " + str(myDataT2[len(myDataT2)-1]) + "C @ " + currTime + ".")

    # Label up some stats...
    ax.text(0.015, 0.05, 'Min: ' + str(lowestOutTemp) + 'C, Max: ' + str(highestOutTemp) + 'C',
        horizontalalignment='left',
        verticalalignment='center',
        fontsize=14, color='blue',
        transform=ax.transAxes)

    ax.text(0.015, 0.1, 'Min: ' + str(lowestInTemp) + 'C, Max: ' + str(highestInTemp) + 'C',
        horizontalalignment='left',
        verticalalignment='center',
        fontsize=14, color='red',
        transform=ax.transAxes)
        
    ax.set_ylabel('C')
    plt.ylim(lowestTemp - 2, highestTemp + 2)
    saveName = savePath + "temp_both.png"
    ax.plot(myDataT1, "r-")
    ax.plot(myDataT2, "b-")

    plt.xlim(0, file_len(theFile))
    # Remove 0 - 1440 values from X-axis.
    frame = plt.gca()
    frame.axes.get_xaxis().set_ticklabels([])

    # Save PNG file for use on web page.
    plt.savefig(saveName, bbox_inches='tight')
    plt.close(fig)
    
# ---------------------
# Main program starts here
# ----------

# Take preliminary reading prior to starting loop.
sense = SenseHat()
humidity = round(sense.get_humidity(), 1)
pressure = round(sense.get_pressure(), 1)
cpuTemp=int(float(getCPUtemperature()))
ambient = sense.get_temperature_from_pressure()
calctemp = round(ambient - ((cpuTemp - ambient)/ 1.5), 1)

while True:
    # Poll sensors
    calctemp, humidity, pressure, cpu_temp = getSensorData(calctemp, humidity, pressure)

    if DS18B20_connected == True:
         temp2 = read_temp2()
    
    # Plot temperature...
    theFile = savePath + "t_data.txt"
    plotGraph(theFile, "T", calctemp)

    # Plot humidity...
    theFile = savePath + "h_data.txt"
    plotGraph(theFile, "H", humidity)

    # Plot pressure...
    theFile = savePath + "p_data.txt"
    plotGraph(theFile, "P", pressure)

    # Plot CPU temperature...
    theFile = savePath + "cpu_data.txt"
    plotGraph(theFile, "T3", cpu_temp)

    if DS18B20_connected == True:
         theFile = savePath + "t2_data.txt"
         plotGraph(theFile, "T2", temp2)
         plotDualGraph(savePath + "t_data.txt", theFile)
         
    # Submit data to InitialState stream...
    #streamer.log("Temperature", temp)
    #streamer.log("Humidity", humidity)
    #streamer.log("Pressure", pressure)

    # Enable for debugging.
    #print("Temperature: %sC" % calctemp)
    #print("Humidity: %s%%rH" % humidity)
    #print("Pressure: %s Millibars" % pressure)

    time.sleep(60) # Set to 2 for debugging, 60 when live.
