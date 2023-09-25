import serial
import time
import os
import sys
import keyboard
import tkinter as tk
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from lib.plantoid.serial_utils import setup_serial
from utils.util import load_config

def mock_arduino_keyboard_input(ser):

    def on_key_press(event):
        if event.char == 'a':
            ser.write(b'button_pressed\n')
            print("Sent 'button_pressed'")

    try:
        root = tk.Tk()
        root.title('Arduino Simulator')
        root.geometry('750x100')
        root.bind('<KeyPress>', on_key_press)

        label = tk.Label(root, text="Press the 'a' key to make plantoid do funny stuff.", font=('', 20))
        label.pack(pady=20)

        root.mainloop()

        ser.close()

    except KeyboardInterrupt:
        print("Program stopped by the user.")
        ser.close()




if __name__ == "__main__":

    config = load_config('../configuration.toml')

    cfg = config['general']

    PORT = cfg['SERIAL_PORT_INPUT']

    ser = setup_serial(PORT=PORT)
    mock_arduino_keyboard_input(ser)