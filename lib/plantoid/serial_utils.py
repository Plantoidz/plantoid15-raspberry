import serial
import keyboard
import time
import os, signal
import random
import regex_spm


def setup_serial(PORT="/dev/ttyUSB0", baud_rate=115200): # 9600 for P14 -- 115200 for P16

    try:

        if PORT is None: raise Exception('No Serial Port Provided!')

        print("setting up serial with PORT = ", PORT);
        # configure the serial connections (the parameters differs on the device you are connecting to)
        ser = serial.Serial(port=PORT, baudrate=baud_rate)

        print("Serial port " + PORT + " opened  Baudrate " + str(baud_rate))

        return ser
        #waitForArduino()

    except serial.SerialException:

        raise Exception('Cannot access provided serial port!')


def send_to_arduino(ser, string_to_send):

    if ser is None:
        raise Exception('Serial cannot be None!')

    start_marker = '<'
    end_marker = '>'

    string_with_markers = start_marker + string_to_send + end_marker

    print('serial string is:', string_with_markers)

    ser.write(string_with_markers.encode('utf-8')) # encode needed for Python3


data_started = False
data_buf = ""
message_complete = False

def check_received_arduino_signal(ser):

    if ser is None:
        raise Exception('Serial cannot be None!')

    start_marker = '<'
    end_marker = '>'
    global data_started
    global data_buf
    global message_complete


    if ser.inWaiting() > 0 and message_complete == False:

        try:
            # decode needed for Python3 
            x = ser.read().decode("utf-8", errors='ignore') # ser.readline().decode('utf-8').strip()
        except Exception as e:
            print(f"Read error: {e}")
            data = ""



        print("["+x+"]")


        if data_started == True:

            if x != end_marker:
                data_buf = data_buf + x
            else:
                data_started = False
                message_complete = True

            print("databuf = " , data_buf); 

        elif x == start_marker:

            data_buf = ''
            data_started = True

        print("["+x+"] == ["+ start_marker+"] == ",  x == start_marker)


    if message_complete == True:

        message_complete = False
        return data_buf

    else:

        return "XXX" 


def use_serial_pattern(use_raspberry):

    if use_raspberry == True:

        # pattern = r"<(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3})>"
        pattern = r"<Touched>"

    else:

        pattern = "button_pressed"

    return pattern


#==================

def wait_for_arduino(ser):

    # wait until the Arduino sends 'Arduino is ready' - allows time for Arduino reset
    # it also ensures that any bytes left over from a previous message are discarded


    print("Waiting for Arduino to reset")


    send_to_arduino(ser, "RESET")
    
    msg = ""

#    start_signal = "<>".encode()
#    serialPort.read_until(start_signal)

    while msg.find("Arduino is ready") == -1:

        print("inside the reset loop")
        send_to_arduino(ser, "RESET")

        msg = check_received_arduino_signal(ser)

        if not (msg == 'XXX'):

            print("[",msg,"]")

    print("ARDUINO IS READY")



def reset_arduino_software(ser):
    ser.write(b'<RESET>\n')
    time.sleep(2)
    ser.flushInput()
