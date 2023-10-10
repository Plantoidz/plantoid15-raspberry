#!/bin/bash

# Check and delete .tmp_log if it exists
if [ -f .tmp_log ]; then
    rm .tmp_log
fi

# Run your socat command
socat -lf .tmp_log -d -d pty,raw,echo=0 pty,raw,echo=0 &

# Give it a moment to populate the log file
sleep 1

# Extract the port names from the log
SERIAL_PORT_INPUT=$(grep "PTY is" .tmp_log | awk 'NR==1 {print $NF}')
SERIAL_PORT_OUTPUT=$(grep "PTY is" .tmp_log | awk 'NR==2 {print $NF}')

# Overwrite or append SERIAL_PORT_INPUT to "../.env"
if grep -q "SERIAL_PORT_INPUT=" "../.env"; then
    sed -i .bak "s|SERIAL_PORT_INPUT=.*|SERIAL_PORT_INPUT=${SERIAL_PORT_INPUT}|" "../.env"
else
    echo "SERIAL_PORT_INPUT=${SERIAL_PORT_INPUT}" >> "../.env"
fi

# Overwrite or append SERIAL_PORT_OUTPUT to ../.env
if grep -q "SERIAL_PORT_OUTPUT=" "../.env"; then
    sed -i .bak "s|SERIAL_PORT_OUTPUT=.*|SERIAL_PORT_OUTPUT=${SERIAL_PORT_OUTPUT}|" "../.env"
else
    echo "SERIAL_PORT_OUTPUT=${SERIAL_PORT_OUTPUT}" >> "../.env"
fi

# Optionally remove the log file
# rm .tmp_log
