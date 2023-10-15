import serial
import time
import os
import sys
import keyboard
import tkinter as tk
from pathlib import Path
from dotenv import load_dotenv
import subprocess

sys.path.append(str(Path(__file__).resolve().parent.parent))

from lib.plantoid.serial_utils import setup_serial
from utils.util import load_config

load_dotenv()

def mock_arduino_keyboard_input(ser):

    def on_key_press(event):
        if event.char == 'a':
            ser.write(b'button_pressed\n')
            print("Sent 'button_pressed'")

    def check_serial_buffer():
        # Read the current serial buffer
        data = ser.read(ser.in_waiting)
        if data:
            print('serial buffer data is:')
            print(data.decode('utf-8'))

        # Schedule this function to run again after 1000 milliseconds (1 second).
        # You can adjust this value to change the frequency of checking the buffer.
        root.after(1000, check_serial_buffer)

    try:
        root = tk.Tk()
        root.title('Arduino Simulator')
        root.geometry('750x100')
        root.bind('<KeyPress>', on_key_press)

        label = tk.Label(root, text="Press the 'a' key to make plantoid do funny stuff.", font=('', 20))
        label.pack(pady=20)

        # Start checking the serial buffer immediately when the UI is displayed
        check_serial_buffer()

        root.mainloop()

        ser.close()
        
        # NOTE: this means you should run the bash script again after closing from the UI
        kill_process('socat') 

    except KeyboardInterrupt:
        print("Program stopped by the user.")
        ser.close()


def kill_process(process_name):
    try:
        # Run the command to get the process IDs of all 'process_name' processes
        result = subprocess.check_output(["pgrep", process_name], stderr=subprocess.STDOUT)
        
        # Split the output to get individual PIDs
        pids = result.decode('utf-8').split()

        # Kill each PID
        for pid in pids:
            subprocess.check_call(["kill", "-9", pid])
        
        print(f"Killed {len(pids)} instances of {process_name}.")

    except subprocess.CalledProcessError:
        # No 'socat' processes found
        print(f"No {process_name} processes running.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":

    config = load_config('../configuration.toml')

    cfg = config['general']

    # PORT = cfg['SERIAL_PORT_INPUT']

    PORT = os.environ.get('SERIAL_PORT_INPUT')

    ser = setup_serial(PORT=PORT)
    mock_arduino_keyboard_input(ser)