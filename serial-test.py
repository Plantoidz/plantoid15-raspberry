import serial
import time

ser = serial.Serial(port="/dev/ttyACM0", baudrate=115200)
print("Serial port opened, waiting for Arduino to reset...")
time.sleep(3)

print("Reading from serial...")
while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        print(f"Received: '{line}'")
        if "Arduino is ready" in line:
            print("Found ready message!")
            break
