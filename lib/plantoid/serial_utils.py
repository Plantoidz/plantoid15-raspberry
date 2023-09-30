import serial
import keyboard
import time
import os, signal
import random
import regex_spm



startMarker = '<'
endMarker = '>'
dataStarted = False
dataBuf = ""
messageComplete = False


#========================
#========================
    # the functions

def setup_serial(PORT="/dev/ttyUSB0", baud_rate=9600):

    if PORT is None: raise Exception('No Serial Port Provided!')

    # configure the serial connections (the parameters differs on the device you are connecting to)
    ser = serial.Serial(port=PORT, baudrate=baud_rate)

    print("Serial port " + PORT + " opened  Baudrate " + str(baud_rate))

    return ser
    #waitForArduino()

#========================

def sendToArduino(stringToSend):

        # this adds the start- and end-markers before sending
    global startMarker, endMarker, serialPort

    stringWithMarkers = (startMarker)
    stringWithMarkers += stringToSend
    stringWithMarkers += (endMarker)

    serialPort.write(stringWithMarkers.encode('utf-8')) # encode needed for Python3


#==================

def recvLikeArduino():

    global startMarker, endMarker, serialPort, dataStarted, dataBuf, messageComplete

    if serialPort.inWaiting() > 0 and messageComplete == False:
        x = serialPort.read().decode("utf-8") # decode needed for Python3

        if dataStarted == True:
            if x != endMarker:
                dataBuf = dataBuf + x
            else:
                dataStarted = False
                messageComplete = True
        elif x == startMarker:
            dataBuf = ''
            dataStarted = True

    if (messageComplete == True):
        messageComplete = False
        return dataBuf

    else:
        return "XXX"


#==================

def waitForArduino():

    # wait until the Arduino sends 'Arduino is ready' - allows time for Arduino reset
    # it also ensures that any bytes left over from a previous message are discarded

    print("Waiting for Arduino to reset")

    msg = ""

#    start_signal = "<>".encode()
#    serialPort.read_until(start_signal)

    while msg.find("Arduino is ready") == -1:
        msg = recvLikeArduino()
        if not (msg == 'XXX'):
            print(msg)


