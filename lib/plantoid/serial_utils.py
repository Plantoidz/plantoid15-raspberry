import serial
import keyboard
import time
import os, signal
import random
import regex_spm
import re

def setup_serial(PORT="/dev/ttyACM0", baud_rate=115200):

    try:

        if PORT is None: raise Exception('No Serial Port Provided!')

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

    string_with_markers = start_marker + string_to_send + end_marker + '\n'

    # print('serial string is:', string_with_markers)

    ser.write(string_with_markers.encode('utf-8')) # encode needed for Python3
    ser.flush()


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

        # decode needed for Python3 
        x = ser.read().decode("utf-8") # ser.readline().decode('utf-8').strip()


        # print("["+x+"]")


        if data_started == True:

            if x != end_marker:
                data_buf = data_buf + x
            else:
                data_started = False
                message_complete = True

            # print("databuf = " , data_buf); 

        elif x == start_marker:

            data_buf = ''
            data_started = True

        # print("["+x+"] == ["+ start_marker+"] == ",  x == start_marker)


    if message_complete == True:

        message_complete = False
        return data_buf

    else:

        return "XXX" 


def use_serial_pattern(use_raspberry):

    if use_raspberry == True:

        pattern = r"<(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3}),\s*(-?\d{1,3})>"

    else:

        pattern = "button_pressed"

    return pattern


#==================

def wait_for_arduino(ser):

    # wait until the Arduino sends 'Arduino is ready' - allows time for Arduino reset
    # it also ensures that any bytes left over from a previous message are discarded

    print("sending RESET signal")
    
    send_to_arduino(ser, "RESET")
    
    print("Waiting for Arduino to reset")

    msg = ""

#    start_signal = "<>".encode()
#    serialPort.read_until(start_signal)

    while msg.find("Arduino is ready") == -1:

        send_to_arduino(ser, "RESET")

        msg = check_received_arduino_signal(ser)

        if not (msg == 'XXX'):

            print("[",msg,"]")

    ser.flushInput()
    print("ARDUINO IS READY")




def reset_arduino_software(ser):
    ser.write(b'<RESET>\n')
    time.sleep(2)
    ser.flushInput()




def check_if_talk(ser, pattern):

    if ser.in_waiting > 0:

        try:


            # line = ser.readline().decode('utf-8').strip()

            # Drain buffer, keep last line
            raw = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            lines = raw.strip().split('\n')
            line = lines[-1].strip()

            print("line ==== ", line, " with pattern ============= ", pattern)

            # Clear the buffer after reading to ensure no old "button_pressed" events are processed.
            ser.reset_input_buffer()
                        
            condition = bool(re.fullmatch(pattern, line))
            return condition

        except UnicodeDecodeError:  
            print("Received a line that couldn't be decoded!")
