# Plantoid

## Run with mocking arduino

You need 3 terminals

T1: cd into /mock_arduino and run bash mock-arduino-ports.sh
Copy the ports it shows into configuration.toml and save the file

T2: also cd into /mock_arduino and run python mock_arduino.py
This gives you the UI button

T3: in the root directory, run python Plantoid15.py
Then press the UI button for execution
