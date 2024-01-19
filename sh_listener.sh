
#!/usr/bin/bash
echo "this script was run by $(whoami)"

# runuser -u pi whoami
#/usr/bin/pulseaudio --system --fail=1 --daemonize=1 --disallow-module-loading --disallow-exit

# /usr/local/bin/python3 -u /home/pi/PLLantoid/v4/listener.py & > /home/pi/PLLantoid/v4/logs/plantony.log  2>&1

#/usr/local/bin/python3 -u /home/pi/PLLantoid/v4/Arduinoserial.py > /home/pi/PLLantoid/v4/logs/plantony.log  2>&1

# /usr/local/bin/python3 -u /home/pi/PLLantoid/v4/listener-goerli.py & > /home/pi/PLLantoid/v4/logs/listen-goerli.log 2>&1

# runuser -l pi -c 'whoami; /usr/local/bin/python3 -u /home/pi/PLLantoid/v4/Arduinoserial.py > /home/pi/PLLantoid/v4/logs/plantony.log  2>&1'

# runuser -u pi /usr/local/bin/python3 -u /home/pi/PLLantoid/v4/listener.py > /home/pi/PLLantoid/v4/logs/plantony.log  2>&1
# runuser -u pi /usr/local/bin/python3 '/home/pi/PLLantoid/v4/listener.py'


# /usr/local/bin/python3 -u /home/pi/PLLantoid/plantoid15-raspberry/Plantoid15.py &  > /home/pi/PLLantoid/v4/logs/AIplantony.log 2>&1


export USE_RASPBERRY=True
export USE_ARDUINO=True
export RASPBERRY_PATH=/home/pi/PLLantoid/plantoid-raspberry/plantoid15-raspberry/
export PYTHONPATH=/home/pi/.local/lib/python3.10/site-packages
/usr/bin/python3.10 -u /home/pi/PLLantoid/plantoid-raspberry/plantoid15-raspberry/Plantoid.py  > /home/pi/PLLantoid/plantoid-raspberry/plantoid15-raspberry/logs/AIplantony.log 2>&1

